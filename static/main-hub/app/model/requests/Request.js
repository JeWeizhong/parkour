Ext.define('MainHub.model.requests.Request', {
    extend: 'MainHub.model.Base',

    fields: [
        {
            type: 'int',
            name: 'id'
        },
        {
            type: 'string',
            name: 'name'
        },
        {
            type: 'int',
            name: 'user'
        },
        {
            type: 'string',
            name: 'user_full_name'
        },
        {
            type: 'date',
            name: 'create_time'
        },
        {
            type: 'string',
            name: 'description'
        },
        {
            type: 'bool',
            name: 'restrict_permissions'
        },
        {
            type: 'string',
            name: 'deep_seq_request_name'
        },
        {
            type: 'string',
            name: 'deep_seq_request_path'
        },
        {
            type: 'float',
            name: 'total_sequencing_depth'
        },
        {
            type: 'auto',
            name: 'files'
        }
    ]
});
