-- 점수	- 기준
-- 1.00	- ideal
-- 0.99	- 동일 column
-- 0.95	- 동일 column, suffix 다름, 선호 suffix
-- 0.90	- 동일 column, suffix 다름, 비선호 suffix
-- 0.89	- 동일 column, prefix 다름
-- 0.85	- 동일 column, prefix/suffix 다름, 선호 suffix
-- 0.80	- 동일 column, prefix/suffix 다름, 비선호 suffix
-- 0.70	- 동일 속성으로 분류 가능
-- 0.50	- 하위속성/유사속성
INSERT INTO column_relation (catalog_column, correlation, metadata_column)
VALUES ('publisher', 0.50,
        'dcat:Catalog.dcat:service.dcat:DataService.dcat:contactPoint.vcard:Organization.vcard:hasTelephone.rdf:resource'),
       ('issued', 0.95, 'dcat:Catalog.dcat:service.dcat:DataService.dct:issued.rdf:datatype:date'),
       ('landing_page', 0.70, 'url'),
       ('modified', 0.95, 'dateModified'),
       ('publisher', 0.50,
        'dcat:Catalog.dcat:service.dcat:DataService.dcat:contactPoint.vcard:Organization.vcard:organization-unit'),
       ('title', 0.99, 'name'),
       ('description', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dct:description'),
       ('title', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dct:title'),
       ('keyword', 0.99, 'keywords'),
       ('publisher', 0.50, 'dcat:Catalog.dcat:service.dcat:DataService.dct:publisher.foaf:Organization.foaf:name'),
       ('landing_page', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:landingPage.rdf:resource'),
       ('issued', 0.70, 'datePublished'),
       ('publisher', 0.50, 'creator.contactPoint.telephone'),
       ('theme', 0.70, 'additionalType'),
       ('publisher', 0.50, 'creator.name'),
       ('modified', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dct:modified.rdf:datatype:date'),
       ('theme', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:theme'),
       ('issued', 0.70, 'dateCreated'),
       ('publisher', 0.50, 'creator.contactPoint.contactType'),
       ('landing_page', 0.50, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:accessURL.rdf:resource'),
       ('keyword', 0.89, 'dcat:Catalog.dcat:service.dcat:DataService.dcat:keyword'),
       ('description', 0.99, 'description');