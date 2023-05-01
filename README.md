# PTO_construction

### Автоматизация рутинных задач для инженеров ПТО в строительстве.
<p>Класс для создания и удаления актов АОСР по шаблону в формате MS Word.docx, используя 
две базы данные в формате csv, где в одной бд используются переменные для акта со связью 
один к одному, а другая бд используется для формирования списков к акту 
подтверждающих документов (сертификаты, паспорта) со связью многие ко многим.
</p> 

#### Список необходимых переменных.
<p>для базы данные value_aosr.csv</p>

- id;
- name_akt;
- number_akt;
- corpus;
- text_works;
- text_sys;
- text_materials;
- heights_sys;
- axis_sys;
- works_input;
- project_RD;
- lists_RD;
- lab_exp;
- Data_first;
- Data_second;
- according;
- work_permit;
- signature_Developer;
- signature_General_Contractor;
- signature_General_Designer;
- signature_Construction_Control;
- signature_Contractor;
- signature_Other_Persons;
- Order_Developer;
- Order_General_Contractor;
- Order_General_Designer;
- Order_Construction_Control;
- Order_Contractor;
- Order_Other_Persons;
- lists_ID;
- construction_object;

<p>для базы данные value_bd.csv</p>

- id_doc;
- transmitted;
- page;
- full_certificate_name;
- full_materials_name;
- materials_name;
- technical_data;
- technical_data2;
- normative_document;
- document_name;
- serial_number;
- date;
- producer;
- folder_number;
- systems;
- notes;
- quantity;
