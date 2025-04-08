from app.schemas.items import CreateItemsRequestModel

get_item_normal_example = {
    "summary": "아이템 가져오기 기본 예제",
    "description": "아이템 가져오기",
    "value": "plumbus"
}
get_item_examples = {
    "normal": get_item_normal_example
}

update_item_normal_example = {
    "summary": "아이템 업데이트 기본 예제",
    "description": "아이템 업데이트",
    "value": "plumbus"
}

update_item_examples = {
    "normal": update_item_normal_example
}

create_item_normal_example = {
    "summary": "아이템 생성 기본 예제",
    "description": "아이템 생성",
    "value": CreateItemsRequestModel(name="apple", status="in stock", stock=10)
}

create_item_examples = {
    "normal": create_item_normal_example
}
