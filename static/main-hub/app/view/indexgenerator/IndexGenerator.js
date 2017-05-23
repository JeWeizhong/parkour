Ext.define('MainHub.view.indexgenerator.IndexGenerator', {
    extend: 'Ext.container.Container',
    xtype: 'index-generator',
    id: 'poolingContainer',

    requires: [
        'MainHub.view.indexgenerator.IndexGeneratorController'
    ],

    controller: 'index-generator',

    layout: {
        type: 'hbox',
        align: 'stretch'
    },
    padding: 15,

    initComponent: function() {
        var me = this;
        me.items = [{
                xtype: 'grid',
                id: 'indexGeneratorTable',
                itemId: 'indexGeneratorTable',
                height: Ext.Element.getViewportHeight() - 94,
                margin: '0 15px 0 0',
                flex: 1,
                header: {
                    title: 'Libraries and Samples for Pooling',
                    items: [{
                        xtype: 'combobox',
                        id: 'poolSizeCb',
                        itemId: 'poolSizeCb',
                        queryMode: 'local',
                        displayField: 'name',
                        valueField: 'id',
                        forceSelection: true,
                        cls: 'panel-header-combobox',
                        fieldLabel: 'Pool Size',
                        labelWidth: 65,
                        width: 170,
                        store: 'poolSizesStore'
                    }]
                },
                viewConfig: {
                    // loadMask: false,
                    stripeRows: false
                    // markDirty: false
                },
                store: 'indexGeneratorStore',
                rootVisible: false,
                sortableColumns: false,
                columns: [{
                        xtype: 'checkcolumn',
                        itemId: 'checkColumn',
                        dataIndex: 'selected',
                        tdCls: 'no-dirty',
                        width: 40
                    },
                    {
                        text: 'Name',
                        dataIndex: 'name',
                        minWidth: 200,
                        flex: 1
                    },
                    {
                        text: 'Barcode',
                        dataIndex: 'barcode',
                        width: 90
                    },
                    {
                        text: '',
                        dataIndex: 'recordType',
                        width: 35
                    },
                    {
                        text: 'Depth (M)',
                        tooltip: 'Sequencing Depth',
                        dataIndex: 'sequencingDepth',
                        width: 85
                    },
                    {
                        text: 'Length',
                        tooltip: 'Read Length',
                        dataIndex: 'read_length',
                        width: 70,
                        editor: {
                            xtype: 'combobox',
                            queryMode: 'local',
                            valueField: 'id',
                            displayField: 'name',
                            store: 'readLengthsStore',
                            matchFieldWidth: false,
                            forceSelection: true
                        },
                        renderer: function(value) {
                            var store = Ext.getStore('readLengthsStore');
                            var record = store.findRecord('id', value)
                            return (record) ? record.get('name') : '';
                        }
                    },
                    {
                        text: 'Protocol',
                        tooltip: 'Library Preparation Protocol',
                        dataIndex: 'libraryProtocolName',
                        width: 150
                    },
                    {
                        text: 'Index Type',
                        dataIndex: 'index_type',
                        width: 150,
                        editor: {
                            id: 'indexTypePoolingEditor',
                            xtype: 'combobox',
                            queryMode: 'local',
                            displayField: 'name',
                            valueField: 'id',
                            store: 'indexTypesStore',
                            matchFieldWidth: false,
                            forceSelection: true
                        },
                        renderer: function(value) {
                            var store = Ext.getStore('indexTypesStore');
                            var record = store.findRecord('id', value)
                            return (record) ? record.get('name') : '';
                        }
                    },
                    {
                        text: 'Index I7',
                        dataIndex: 'indexI7',
                        width: 100
                    },
                    {
                        text: 'Index I5',
                        dataIndex: 'indexI5',
                        width: 100
                    }
                ],
                plugins: [{
                    ptype: 'rowediting',
                    clicksToEdit: 1
                }],
                features: [{
                    ftype: 'grouping',
                    groupHeaderTpl: [
                        '<strong>Request: {children:this.getName}</strong> (Depth: {children:this.getTotalDepth})',
                        {
                            getName: function(children) {
                                return children[0].get('requestName');
                            },
                            getTotalDepth: function(children) {
                                return Ext.sum(Ext.pluck(Ext.pluck(children, 'data'), 'sequencingDepth'));;
                            }
                        }
                    ]
                }]
            },
            {
                xtype: 'grid',
                id: 'poolGrid',
                itemId: 'poolGrid',
                cls: 'pooling-grid',
                header: {
                    title: 'Pool',
                    height: 56
                },
                height: Ext.Element.getViewportHeight() - 94,
                flex: 1,
                features: [{
                    ftype: 'summary'
                }],
                viewConfig: {
                    markDirty: false
                },
                problematicCycles: [],
                sortableColumns: false,
                columns: [{
                        text: 'Name',
                        dataIndex: 'name',
                        width: 200
                    },
                    {
                        text: '',
                        dataIndex: 'recordType',
                        width: 35
                    },
                    {
                        text: 'Depth (M)',
                        dataIndex: 'sequencingDepth',
                        width: 85,
                        summaryType: 'sum',
                        summaryRenderer: function(value) {
                            return (value > 0) ? value : '';
                        }
                    },
                    {
                        text: 'Index I7 ID',
                        dataIndex: 'indexI7Id',
                        width: 90,
                        summaryRenderer: function() {
                            var totalSequencingDepth = Ext.getCmp('poolGrid').getStore().sum('sequencingDepth');
                            return (totalSequencingDepth > 0) ? '<span class="summary-green">green:</span><br><span class="summary-red">red:</span>' : '';
                        }
                    },
                    {
                        text: '1',
                        dataIndex: 'indexI7_1',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '2',
                        dataIndex: 'indexI7_2',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '3',
                        dataIndex: 'indexI7_3',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '4',
                        dataIndex: 'indexI7_4',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '5',
                        dataIndex: 'indexI7_5',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '6',
                        dataIndex: 'indexI7_6',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '7',
                        dataIndex: 'indexI7_7',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        width: 55
                    },
                    {
                        text: '8',
                        dataIndex: 'indexI7_8',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        width: 55
                    },
                    {
                        text: 'Index I5 ID',
                        dataIndex: 'indexI5Id',
                        summaryRenderer: function() {
                            var totalSequencingDepth = Ext.getCmp('poolGrid').getStore().sum('sequencingDepth');
                            return (totalSequencingDepth > 0) ? '<span class="summary-green">green:</span><br><span class="summary-red">red:</span>' : '';
                        },
                        width: 90
                    },
                    {
                        text: '1',
                        dataIndex: 'indexI5_1',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '2',
                        dataIndex: 'indexI5_2',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '3',
                        dataIndex: 'indexI5_3',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '4',
                        dataIndex: 'indexI5_4',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '5',
                        dataIndex: 'indexI5_5',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '6',
                        dataIndex: 'indexI5_6',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        summaryType: me.calculateColorDiversity,
                        summaryRenderer: me.renderSummary,
                        width: 55
                    },
                    {
                        text: '7',
                        dataIndex: 'indexI5_7',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        width: 55
                    },
                    {
                        text: '8',
                        dataIndex: 'indexI5_8',
                        cls: 'nucleotide-header',
                        renderer: me.renderCell,
                        width: 55
                    }
                ],
                store: [],
                bbar: [{
                        xtype: 'button',
                        id: 'generateIndices',
                        itemId: 'generateIndices',
                        iconCls: 'fa fa-cogs fa-lg',
                        text: 'Generate Indices',
                        disabled: true
                    },
                    '->',
                    {
                        xtype: 'button',
                        id: 'savePool',
                        itemId: 'savePool',
                        iconCls: 'fa fa-floppy-o fa-lg',
                        text: 'Save Pool',
                        disabled: true
                    }
                ]
            }
        ];

        me.callParent(arguments);
    },

    renderCell: function(val, meta) {
        if (val === 'G' || val === 'T') {
            meta.tdStyle = 'background-color:#dcedc8';
        } else if (val === 'A' || val === 'C') {
            meta.tdStyle = 'background-color:#ef9a9a';
        }
        meta.tdCls = 'nucleotide';
        return val;
    },

    calculateColorDiversity: function(records, values) {
        var diversity = {
            green: 0,
            red: 0
        };

        for (var i = 0; i < values.length; i++) {
            var nuc = values[i];
            if (nuc !== ' ' && typeof nuc !== 'undefined') {
                if (nuc === 'G' || nuc === 'T') {
                    diversity.green += records[i].get('sequencingDepth');
                } else if (nuc === 'A' || nuc === 'C') {
                    diversity.red += records[i].get('sequencingDepth');
                }
            }
        }

        return diversity;
    },

    renderSummary: function(value, summaryData, dataIndex) {
        var result = '',
            grid = Ext.getCmp('poolGrid'),
            totalSequencingDepth = 0;

        if (value.green > 0 || value.red > 0) {
            if (dataIndex.split('_')[0] === 'indexI7') {
                // Consider only non empty Index I7 indices
                grid.getStore().each(function(record) {
                    if (record.get('indexI7') !== '') {
                        totalSequencingDepth += record.get('sequencingDepth');
                    }
                });
            } else {
                // Consider only non empty Index I5 indices
                grid.getStore().each(function(record) {
                    if (record.get('indexI5') !== '') {
                        totalSequencingDepth += record.get('sequencingDepth');
                    }
                });
            }

            var green = parseInt(((value.green / totalSequencingDepth) * 100).toFixed(0)),
                red = parseInt(((value.red / totalSequencingDepth) * 100).toFixed(0));

            result = green + '%' + '<br>' + red + '%';

            if ((green < 20 && red > 80) || (red < 20 && green > 80)) {
                result += '<br>!';

                // Remember the cell in order to highlight it after summary refresh
                if (grid.problematicCycles.indexOf(this.id) === -1) {
                    grid.problematicCycles.push(this.id);
                }
            }
        }

        return result;
    }
});
