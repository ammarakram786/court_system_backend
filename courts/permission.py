from accounts.models import Permission

COURT_PERMISSIONS = [
    # Court
    Permission(name='Create Court', code_name='court_create', module_name='Court', app_name='courts', description='User can create court'),
    Permission(name='Read Court', code_name='court_read', module_name='Court', app_name='courts', description='User can read court'),
    Permission(name='Update Court', code_name='court_update', module_name='Court', app_name='courts', description='User can update court'),
    Permission(name='Delete Court', code_name='court_delete', module_name='Court', app_name='courts', description='User can delete court'),

    # Police Station
    Permission(name='Create Police Station', code_name='police_station_create', module_name='PoliceStation', app_name='courts', description='User can create police station'),
    Permission(name='Read Police Station', code_name='police_station_read', module_name='PoliceStation', app_name='courts', description='User can read police station'),
    Permission(name='Update Police Station', code_name='police_station_update', module_name='PoliceStation', app_name='courts', description='User can update police station'),
    Permission(name='Delete Police Station', code_name='police_station_delete', module_name='PoliceStation', app_name='courts', description='User can delete police station'),

    # Case Category
    Permission(name='Create Case Category', code_name='case_category_create', module_name='CaseCategory', app_name='courts', description='User can create case category'),
    Permission(name='Read Case Category', code_name='case_category_read', module_name='CaseCategory', app_name='courts', description='User can read case category'),
    Permission(name='Update Case Category', code_name='case_category_update', module_name='CaseCategory', app_name='courts', description='User can update case category'),
    Permission(name='Delete Case Category', code_name='case_category_delete', module_name='CaseCategory', app_name='courts', description='User can delete case category'),

    # Case
    Permission(name='Create Case', code_name='case_create', module_name='Case', app_name='courts', description='User can create case'),
    Permission(name='Read Case', code_name='case_read', module_name='Case', app_name='courts', description='User can read case'),
    Permission(name='Update Case', code_name='case_update', module_name='Case', app_name='courts', description='User can update case'),
    Permission(name='Delete Case', code_name='case_delete', module_name='Case', app_name='courts', description='User can delete case'),
    Permission(name='Close Case', code_name='case_close', module_name='Case', app_name='courts', description='User can close case'),

    # Case Party
    Permission(name='Create Case Party', code_name='case_party_create', module_name='CaseParty', app_name='courts', description='User can create case party'),
    Permission(name='Read Case Party', code_name='case_party_read', module_name='CaseParty', app_name='courts', description='User can read case party'),
    Permission(name='Update Case Party', code_name='case_party_update', module_name='CaseParty', app_name='courts', description='User can update case party'),
    Permission(name='Delete Case Party', code_name='case_party_delete', module_name='CaseParty', app_name='courts', description='User can delete case party'),

    # Case Proceeding
    Permission(name='Create Case Proceeding', code_name='case_proceeding_create', module_name='CaseProceeding', app_name='courts', description='User can create case proceeding'),
    Permission(name='Read Case Proceeding', code_name='case_proceeding_read', module_name='CaseProceeding', app_name='courts', description='User can read case proceeding'),
    Permission(name='Update Case Proceeding', code_name='case_proceeding_update', module_name='CaseProceeding', app_name='courts', description='User can update case proceeding'),
    Permission(name='Delete Case Proceeding', code_name='case_proceeding_delete', module_name='CaseProceeding', app_name='courts', description='User can delete case proceeding'),

    # Cause List
    Permission(name='Create Cause List', code_name='cause_list_create', module_name='CauseList', app_name='courts', description='User can create cause list'),
    Permission(name='Read Cause List', code_name='cause_list_read', module_name='CauseList', app_name='courts', description='User can read cause list'),
    Permission(name='Update Cause List', code_name='cause_list_update', module_name='CauseList', app_name='courts', description='User can update cause list'),
    Permission(name='Delete Cause List', code_name='cause_list_delete', module_name='CauseList', app_name='courts', description='User can delete cause list'),

    # Cause List Item
    Permission(name='Create Cause List Item', code_name='cause_list_item_create', module_name='CauseListItem', app_name='courts', description='User can create cause list item'),
    Permission(name='Read Cause List Item', code_name='cause_list_item_read', module_name='CauseListItem', app_name='courts', description='User can read cause list item'),
    Permission(name='Update Cause List Item', code_name='cause_list_item_update', module_name='CauseListItem', app_name='courts', description='User can update cause list item'),
    Permission(name='Delete Cause List Item', code_name='cause_list_item_delete', module_name='CauseListItem', app_name='courts', description='User can delete cause list item'),
]

PERMISSIONS = COURT_PERMISSIONS
