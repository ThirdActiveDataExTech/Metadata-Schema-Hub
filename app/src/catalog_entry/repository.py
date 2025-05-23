import json
import re
from datetime import date, datetime
from typing import List

from sqlalchemy import create_engine, event, select
from sqlmodel import Session, select

from app.schemas.catalog_entry import CatalogEntry
from app.src.catalog_entry.config import config


class CatalogEntryRepository:
    """CatalogEntryService."""

    def __init__(self, db_url: str = config.DB_URL, verbose: bool = True):
        """Connect PostgreSQL."""
        self.engine = create_engine(db_url)

        # 엔진에 이벤트 리스너 등록 (한 번만)
        if verbose:
            event.listen(self.engine, "after_cursor_execute", self.log_queries)


    def save(self, catalog_entry: CatalogEntry) -> CatalogEntry:
        """Save catalog_entry."""
        with Session(self.engine) as session:
            session.add(catalog_entry)
            session.commit()
            session.refresh(catalog_entry)
            return catalog_entry

    def save_bulk(self, catalog_entries: List[CatalogEntry]) -> List[CatalogEntry]:
        """Bulk save catalog_entries."""
        if not catalog_entries:
            return []

        with Session(self.engine) as session:
            session.add_all(catalog_entries)
            session.commit()
            for entry in catalog_entries:
                session.refresh(entry)
            return catalog_entries

    def select(self, catalog_entry_id: int) -> CatalogEntry:
        """Select catalog_entry."""
        with Session(self.engine) as session:
            catalog_entry = session.get(CatalogEntry, catalog_entry_id)
        if not catalog_entry:
            raise ValueError(f"{catalog_entry_id=} not found.")

        return catalog_entry


    def export_data_list(self, limit: int = None):
        """데이터베이스의 catalog_entry 테이블 전체를 list로 내보냄."""
        with Session(self.engine) as session:
            # 모든 레코드 조회 쿼리 작성 (필요시 limit 추가)
            statement = select(CatalogEntry)
            if limit:
                statement = statement.limit(limit)

            # 쿼리 실행
            results = session.exec(statement).all()

            if not results:
                print("내보낼 데이터가 없습니다.")
                return None

            # 결과를 딕셔너리 리스트로 변환
            data_list = []
            for result in results:
                # SQLModel 0.0.14부터 dict() 대신 model_dump() 사용
                data = result.model_dump()

                # 날짜 필드 문자열 변환
                if 'issued' in data and data['issued']:
                    data['issued'] = str(data['issued'])

                if 'modified' in data and data['modified']:
                    data['modified'] = str(data['modified'])

                if 'ingested_at' in data and data['ingested_at']:
                    data['ingested_at'] = str(data['ingested_at'])

                if 'updated_at' in data and data['updated_at']:
                    data['updated_at'] = str(data['updated_at'])

                # JSONB 필드는 문자열로 변환하여 CSV에 저장
                if 'publisher' in data and isinstance(data['publisher'], dict):
                    data['publisher'] = json.dumps(data['publisher'], ensure_ascii=False)

                if 'raw_metadata' in data:
                    # raw_metadata는 너무 크고 복잡하므로 CSV에서 제외
                    data.pop('raw_metadata', None)

                # 배열 타입 필드 (keyword, theme)도 문자열로 변환
                if 'keyword' in data and isinstance(data['keyword'], list):
                    data['keyword'] = ','.join(data['keyword']) if data['keyword'] else ''

                if 'theme' in data and isinstance(data['theme'], list):
                    data['theme'] = ','.join(data['theme']) if data['theme'] else ''

                data_list.append(data)

            return data_list


    @staticmethod
    def log_queries(conn, cursor, statement, params, context, executemany):
        """쿼리 로깅 함수."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_dump_{timestamp}.sql"

        with open(filename, 'a', encoding='utf-8') as f:
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
                                    if key == 'raw_metadata' or key == 'publisher':
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
                                param_pattern = f'%\\({key}\\)s'
                                actual_query = re.sub(param_pattern, replacement, actual_query)

                            # 쿼리 끝에 세미콜론 추가
                            if not actual_query.strip().endswith(';'):
                                actual_query = actual_query.strip() + ';'

                            f.write(f"{actual_query}\n\n")
                    # 단일 쿼리인 경우
                    elif isinstance(params, dict):
                        actual_query = statement
                        for key, value in params.items():
                            # 값 타입에 따른 처리
                            if value is None:
                                replacement = "NULL"
                            elif isinstance(value, str):
                                if key == 'raw_metadata' or key == 'publisher':
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

                            param_pattern = f'%\\({key}\\)s'
                            actual_query = re.sub(param_pattern, replacement, actual_query)

                        # 쿼리 끝에 세미콜론 추가
                        if not actual_query.strip().endswith(';'):
                            actual_query = actual_query.strip() + ';'

                        f.write(f"{actual_query}\n\n")
                except Exception as e:
                    f.write(f"-- Error generating actual query: {str(e)}\n")

            f.write("-- " + "-" * 50 + "\n\n")
