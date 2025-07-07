-- 점수 기준
-- 1.00	- ideal
-- 0.99	- 동일 column
-- 0.95	- 동일 column, suffix 다름, 선호 suffix
-- 0.90	- 동일 column, suffix 다름, 비선호 suffix
-- 0.89	- 동일 column, prefix 다름
-- 0.85	- 동일 column, prefix/suffix 다름, 선호 suffix
-- 0.80	- 동일 column, prefix/suffix 다름, 비선호 suffix
-- 0.70	- 동일 속성으로 분류 가능
-- 0.50	- 하위속성/유사속성

-- data.go.kr DCAT 데이터 매핑
INSERT INTO column_relation (catalog_column, correlation, metadata_column)
VALUES ('publisher', 0.50,
        'dcat:Catalog.dcat:service.dcat:DataService.dcat:contactPoint.vcard:Organization.vcard:hasTelephone.rdf:resource'),
       ('issued', 0.95, 'dcat:Catalog.dcat:service.dcat:DataService.dct:issued.rdf:datatype:date'),
       ('publisher', 0.50,
        'dcat:Catalog.dcat:service.dcat:DataService.dcat:contactPoint.vcard:Organization.vcard:organization-unit'),
       ('description', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dct:description'),
       ('title', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dct:title'),
       ('publisher', 0.50, 'dcat:Catalog.dcat:service.dcat:DataService.dct:publisher.foaf:Organization.foaf:name'),
       ('landing_page', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:landingPage.rdf:resource'),
       ('publisher', 0.50, 'creator.contactPoint.telephone'),
       ('publisher', 0.50, 'creator.name'),
       ('modified', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dct:modified.rdf:datatype:date'),
       ('theme', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:theme'),
       ('publisher', 0.50, 'creator.contactPoint.contactType'),
       ('landing_page', 0.50, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:accessURL.rdf:resource'),
       ('keyword', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:keyword');

-- data.go.kr schema.org 데이터 매핑
INSERT INTO datagokr.public.column_relation (catalog_column, correlation, metadata_column)
VALUES ('landing_page', 0.70, 'url'),
       ('modified', 0.95, 'dateModified'),
       ('title', 0.99, 'name'),
       ('keyword', 0.99, 'keywords'),
       ('issued', 0.70, 'datePublished'),
       ('theme', 0.70, 'additionalType'),
       ('issued', 0.70, 'dateCreated'),
       ('description', 0.99, 'description');

-- KOSIS JSON 통계목록 데이터 매핑
INSERT INTO column_relation (catalog_column, correlation, metadata_column)
VALUES ('title', 0.99, 'TBL_NM'),
       ('identifier', 0.99, 'TBL_ID'),
       ('modified', 0.95, 'SEND_DE'),
       ('publisher', 0.89, 'ORG_ID'),
       ('description', 0.70, 'VW_NM'),
       ('theme', 0.50, 'STAT_ID');

-- KOSIS SDMX 통계목록 데이터 매핑
INSERT INTO column_relation (catalog_column, correlation, metadata_column)
VALUES ('title', 0.99,
        'sdmx-msg:Structure.sdmx-msg:Structures.sdmx-str:CategorySchemes.sdmx-str:CategoryScheme.sdmx-str:Category.sdmx-common:Name'),
       ('identifier', 0.99,
        'sdmx-msg:Structure.sdmx-msg:Structures.sdmx-str:CategorySchemes.sdmx-str:CategoryScheme.sdmx-str:Category.id'),
       ('modified', 0.95,
        'sdmx-msg:Structure.sdmx-msg:Structures.sdmx-str:CategorySchemes.sdmx-str:CategoryScheme.sdmx-str:Category.sdmx-str:SendDe.sdmx-common:Name'),
       ('issued', 0.89, 'sdmx-msg:Structure.sdmx-msg:Header.sdmx-msg:Prepared'),
       ('publisher', 0.99, 'sdmx-msg:Structure.sdmx-msg:Header.sdmx-msg:Sender.sdmx-common:Name'),
       ('description', 0.70,
        'sdmx-msg:Structure.sdmx-msg:Structures.sdmx-str:CategorySchemes.sdmx-str:CategoryScheme.sdmx-common:Name'),
       ('theme', 0.50,
        'sdmx-msg:Structure.sdmx-msg:Structures.sdmx-str:CategorySchemes.sdmx-str:CategoryScheme.sdmx-str:Category.sdmx-str:StatId.sdmx-common:Name');