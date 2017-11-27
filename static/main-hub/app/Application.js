/**
 * The main application class. An instance of this class is created by app.js when it
 * calls Ext.application(). This is the ideal place to handle application launch and
 * initialization details.
 */
Ext.Loader.setConfig({
  enabled: true,
  paths: {
    'Ext.ux': 'static/main-hub/ext/packages/ux/classic/src/'
  }
});

Ext.define('MainHub.Application', {
  extend: 'Ext.app.Application',

  name: 'MainHub',

  appFolder: '/static/main-hub/app',

  stores: [
    'NavigationTree',
    'requests.Requests',
    'requests.RequestFiles',
    'libraries.Libraries',
    'libraries.LibraryProtocols',
    'libraries.LibraryTypes',
    'libraries.Organisms',
    'libraries.IndexTypes',
    'libraries.IndexI7',
    'libraries.IndexI5',
    'libraries.ConcentrationMethods',
    'libraries.ReadLengths',
    'libraries.NucleicAcidTypes',
    'libraries.RNAQuality',
    'incominglibraries.IncomingLibraries',
    'indexgenerator.PoolSizes',
    'requests.LibrariesInRequest',
    'indexgenerator.IndexGenerator',
    'librarypreparation.LibraryPreparation',
    'pooling.Pooling',
    'flowcell.Flowcells',
    'flowcell.Sequencer',
    'flowcell.Lanes',
    'flowcell.Pool',
    'flowcell.PoolInfo'
  ],

  requires: [
    'Ext.ux.ToastMessage'
  ],

  launch: function () {
    // TODO - Launch the application
  },

  onAppUpdate: function () {
    Ext.Msg.confirm('Application Update', 'This application has an update, reload?',
      function (choice) {
        if (choice === 'yes') {
          window.location.reload();
        }
      }
    );
  }
});

Ext.define('MainHub.Utilities', {
  singleton: true,
  getDataIndex: function (e, view) {
    var xPos = e.getXY()[0];
    var columns = view.getGridColumns();
    var dataIndex;

    for (var colIdx in columns) {
      var leftEdge = columns[colIdx].getPosition()[0];
      var rightEdge = columns[colIdx].getSize().width + leftEdge;

      if (xPos >= leftEdge && xPos <= rightEdge) {
        dataIndex = columns[colIdx].dataIndex;
        break;
      }
    }

    return dataIndex;
  }
});

Ext.define('MainHub.grid.SearchInputMixin', {
  changeFilter: function (el, value) {
    var grid = el.up('grid');
    var store = grid.getStore();
    var columns = Ext.pluck(grid.getColumns(), 'dataIndex');

    store.clearFilter();
    store.filterBy(function (record) {
      var res = false;
      Ext.each(columns, function (column) {
        if (
          record.data[column] &&
          record.data[column].toString().toLowerCase().indexOf(value.toLowerCase()) > -1
        ) {
          res = res || true;
        }
      });
      return res;
    });
  }
});

Ext.define('MainHub.grid.CheckboxesAndSearchInputMixin', {
  changeFilter: function (el, value) {
    var grid = el.up('grid');
    var store = grid.getStore();
    var columns = Ext.pluck(grid.getColumns(), 'dataIndex');
    var showLibraries;
    var showSamples;
    var searchQuery;

    if (el.itemId === 'show-libraries-checkbox') {
      showLibraries = value;
      showSamples = el.up().items.items[1].getValue();
      searchQuery = el.up('header').down('textfield').getValue();
    } else if (el.itemId === 'show-samples-checkbox') {
      showLibraries = el.up().items.items[0].getValue();
      showSamples = value;
      searchQuery = el.up('header').down('textfield').getValue();
    } else if (el.itemId === 'search-field') {
      showLibraries = el.up().down('fieldcontainer').items.items[0].getValue();
      showSamples = el.up().down('fieldcontainer').items.items[1].getValue();
      searchQuery = value;
    }

    var showFilter = Ext.util.Filter({
      filterFn: function (record) {
        var res = false;
        if (record.get('record_type') === 'Library') {
          res = res || showLibraries;
        } else {
          res = res || showSamples;
        }
        return res;
      }
    });

    var searchFilter = Ext.util.Filter({
      filterFn: function (record) {
        var res = false;
        if (searchQuery) {
          Ext.each(columns, function (column) {
            var val = record.get(column);
            if (val && val.toString().toLowerCase().indexOf(searchQuery.toLowerCase()) > -1) {
              res = res || true;
            }
          });
        } else {
          res = true;
        }
        return res;
      }
    });

    store.clearFilter();
    store.filter([showFilter, searchFilter]);
  }
});
