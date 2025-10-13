import json
import logging
import re
from datetime import date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel

from app.config import settings

connect_args = {}
postgres_url: str = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_engine(postgres_url, connect_args=connect_args)



def create_db_and_tables():
    """Create db and tables."""
    try:
        SQLModel.metadata.create_all(engine)
    except SQLAlchemyError as e:
        logging.error(f"Database initialization failed while creating tables: {e}")
        raise
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        raise


def log_queries(conn, cursor, statement, params, context, executemany):
    """쿼리 로깅 함수."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"query_dump_{timestamp}.sql"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"-- Executed at: {datetime.now()}\n\n")

        # 실제 값으로 대체된 쿼리 생성
        if params:
            try:
                # 배치 쿼리인 경우 (params가 리스트인 경우)
                if isinstance(params, list):
                    for i, param_dict in enumerate(params):
                        # %(name)s 형식의 파라미터를 실제 값으로 대체
                        actual_query = statement
                        for key, value in param_dict.items():
                            # 값 타입에 따른 처리
                            if value is None:
                                replacement = "NULL"
                            elif isinstance(value, str):
                                # JSON 문자열인 경우 UTF-8로 디코딩
                                if key == "raw_metadata" or key == "publisher":
                                    try:
                                        json_obj = json.loads(value)
                                        pretty_json = json.dumps(json_obj, ensure_ascii=False)
                                        replacement = f"'{pretty_json}'"
                                    except:
                                        replacement = f"'{value}'"
                                else:
                                    replacement = f"'{value}'"
                            elif isinstance(value, (list, dict)):
                                # 리스트나 딕셔너리는 JSON으로 변환
                                replacement = f"'{json.dumps(value, ensure_ascii=False)}'"
                            elif isinstance(value, (int, float)):
                                replacement = str(value)
                            elif isinstance(value, date):
                                replacement = f"'{value}'"
                            else:
                                replacement = f"'{value}'"

                            # 파라미터 이름 패턴 (%(name)s)에 맞춰 대체
                            param_pattern = f"%\\({key}\\)s"
                            actual_query = re.sub(param_pattern, replacement, actual_query)

                        # 쿼리 끝에 세미콜론 추가
                        if not actual_query.strip().endswith(";"):
                            actual_query = actual_query.strip() + ";"

                        f.write(f"{actual_query}\n\n")
                # 단일 쿼리인 경우
                elif isinstance(params, dict):
                    actual_query = statement
                    for key, value in params.items():
                        # 값 타입에 따른 처리
                        if value is None:
                            replacement = "NULL"
                        elif isinstance(value, str):
                            if key == "raw_metadata" or key == "publisher":
                                try:
                                    json_obj = json.loads(value)
                                    pretty_json = json.dumps(json_obj, ensure_ascii=False)
                                    replacement = f"'{pretty_json}'"
                                except:
                                    replacement = f"'{value}'"
                            else:
                                replacement = f"'{value}'"
                        elif isinstance(value, (list, dict)):
                            replacement = f"'{json.dumps(value, ensure_ascii=False)}'"
                        elif isinstance(value, (int, float)):
                            replacement = str(value)
                        elif isinstance(value, date):
                            replacement = f"'{value}'"
                        else:
                            replacement = f"'{value}'"

                        param_pattern = f"%\\({key}\\)s"
                        actual_query = re.sub(param_pattern, replacement, actual_query)

                    # 쿼리 끝에 세미콜론 추가
                    if not actual_query.strip().endswith(";"):
                        actual_query = actual_query.strip() + ";"

                    f.write(f"{actual_query}\n\n")
            except Exception as e:
                f.write(f"-- Error generating actual query: {str(e)}\n")

        f.write("-- " + "-" * 50 + "\n\n")


if settings.POSTGRES_VERBOSE:
    event.listen(engine, "after_cursor_execute", log_queries)
