from flask import Flask, render_template, request, jsonify, send_file
from os import path
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
import csv
import io

from src.const import database_header

template_folder = path.abspath('src/frontend/templates')
print(template_folder)

app = Flask(__name__, template_folder=template_folder)
DATABASE = 'data/database.db'

def init_db():
    """初始化数据库，如果不存在则创建"""
    command='''
            CREATE TABLE IF NOT EXISTS data_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ''' + ', '.join([f'{col} TEXT' for col in database_header]) + ''',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
    if not path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(command)
        conn.commit()
        conn.close()

def get_table_info():
    """获取表的列信息"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(data_table)")
    columns = cursor.fetchall()
    conn.close()
    return columns

def get_distinct_values(column):
    """获取指定列的唯一值"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT {column} FROM data_table WHERE {column} IS NOT NULL")
        values = [row[0] for row in cursor.fetchall()]
        conn.close()
        return values
    except:
        return []

@app.route('/')
def index():
    """主页面"""
    columns = get_table_info()
    # 获取每列的唯一值用于筛选
    column_values = {}
    for col in columns:
        if col[1] not in ['id', 'created_at']:  # 排除ID和时间戳列
            values = get_distinct_values(col[1])
            column_values[col[1]] = values
    return render_template('index.html', columns=columns, column_values=column_values)

@app.route('/api/query', methods=['POST'])
def query_data():
    """查询数据API"""
    try:
        data = request.json
        filters = data.get('filters', {})
        page = data.get('page', 1)
        per_page = data.get('per_page', 10)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 构建查询条件和参数
        conditions = []
        params = []
        
        for column, condition in filters.items():
            if condition.get('value'):
                operator = condition.get('operator', '=')
                value = condition.get('value')
                
                if operator == 'like':
                    conditions.append(f"{column} LIKE ?")
                    params.append(f"%{value}%")
                elif operator == '>':
                    conditions.append(f"{column} > ?")
                    params.append(value)
                elif operator == '<':
                    conditions.append(f"{column} < ?")
                    params.append(value)
                elif operator == '>=':
                    conditions.append(f"{column} >= ?")
                    params.append(value)
                elif operator == '<=':
                    conditions.append(f"{column} <= ?")
                    params.append(value)
                elif operator == '!=':
                    conditions.append(f"{column} != ?")
                    params.append(value)
                else:  # 默认使用等于
                    conditions.append(f"{column} = ?")
                    params.append(value)
        
        # 构建查询SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取总数量
        count_sql = f"SELECT COUNT(*) FROM data_table WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]
        
        # 获取数据
        offset = (page - 1) * per_page
        query_sql = f"SELECT * FROM data_table WHERE {where_clause} LIMIT ? OFFSET ?"
        
        cursor.execute(query_sql, params + [per_page, offset])
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        # 转换为字典列表
        result = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            result.append(row_dict)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': result,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'columns': columns
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """上传CSV文件并插入数据（支持多个文件）"""
    print(request.files)
    
    try:
        # 检查是否有文件上传
        if len(request.files) == 0:
            return jsonify({'success': False, 'error': '没有文件上传'})
        
        # 初始化统计信息
        file_stats = {
            'total_files': 0,
            'success_count': 0,
            'failure_count': 0,
            'total_rows_inserted': 0
        }
        
        failed_files = []
        all_new_columns = set()
        
        # 遍历所有上传的文件（file_0, file_1, ...）
        for file_key in request.files:
            file_stats['total_files'] += 1
            file = request.files[file_key]
            
            # 检查文件格式
            if not file.filename.lower().endswith('.csv'):
                file_stats['failure_count'] += 1
                failed_files.append({
                    'filename': file.filename,
                    'error': '文件格式不正确，请上传CSV文件'
                })
                continue

            # 读取CSV文件
            df = pd.read_csv(file)
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # 获取现有表的列
            cursor.execute("PRAGMA table_info(data_table)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # 获取CSV文件的列
            csv_columns = df.columns.tolist()
            print(csv_columns)
            
            # 找出需要添加的新列
            new_columns = [col for col in csv_columns if col not in existing_columns]
            
            # 记录所有新列（用于返回统计）
            for col in new_columns:
                all_new_columns.add(col)
            
            # 添加新列到表
            for column in new_columns:
                # 尝试推断数据类型
                sample_value = None
                if not df[column].dropna().empty:
                    sample_value = df[column].dropna().iloc[0]
                
                if sample_value is not None:
                    if isinstance(sample_value, (int, float)):
                        col_type = 'INTEGER' if isinstance(sample_value, int) else 'REAL'
                    else:
                        col_type = 'TEXT'
                else:
                    col_type = 'TEXT'  # 默认为TEXT

                cursor.execute(f"ALTER TABLE data_table ADD COLUMN {column} {col_type}")


            
            # 更新现有列列表
            cursor.execute("PRAGMA table_info(data_table)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # 准备插入数据
            inserted_count = 0
            for _, row in df.iterrows():
                # 创建列名和值的映射
                row_dict = row.to_dict()
                
                # 只保留表中存在的列
                filtered_row = {k: v for k, v in row_dict.items() if k in existing_columns}
                
                # 构建插入语句
                columns = list(filtered_row.keys())
                if not columns:  # 如果所有列都不匹配，跳过
                    continue
                
                placeholders = ['?' for _ in columns]
                values = [filtered_row[col] for col in columns]
                
                insert_sql = f"INSERT INTO data_table ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                
                try:
                    cursor.execute(insert_sql, values)
                    inserted_count += 1
                except Exception as e:
                    print(f"插入失败: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            # 更新统计信息
            file_stats['success_count'] += 1
            file_stats['total_rows_inserted'] += inserted_count
            
            print(f"文件 {file.filename} 处理完成，插入 {inserted_count} 行")
        
        # 构建响应数据
        response_data = {
            'success': True,
            'success_count': file_stats["success_count"],
            'failure_count': file_stats["failure_count"],
            'total_rows_inserted': file_stats["total_rows_inserted"],
            'new_columns': list(all_new_columns)
        }
        
        # 如果有失败的文件，添加到响应中
        if failed_files:
            response_data['failed_files'] = failed_files
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'系统错误: {str(e)}'
        })

@app.route('/api/delete', methods=['POST'])
def delete_data():
    """删除数据API"""
    try:
        data = request.json
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'error': '没有提供要删除的ID'})
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 构建IN语句
        placeholders = ', '.join(['?' for _ in ids])
        delete_sql = f"DELETE FROM data_table WHERE id IN ({placeholders})"
        
        cursor.execute(delete_sql, ids)
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 条记录',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/columns')
def get_columns():
    """获取表的列信息API"""
    columns = get_table_info()
    return jsonify({
        'success': True,
        'columns': [{'name': col[1], 'type': col[2]} for col in columns]
    })

@app.route('/api/export_query', methods=['POST'])
def export_query():
    """导出查询条件为JSON"""
    try:
        data = request.json
        return jsonify({
            'success': True,
            'query_conditions': data.get('filters', {}),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8000)