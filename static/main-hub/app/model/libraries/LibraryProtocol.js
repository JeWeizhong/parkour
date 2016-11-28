Ext.define('MainHub.model.libraries.LibraryProtocol', {
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
            type: 'string',
            name: 'provider'
        }
    ]
});