(function() {
  'use strict';

  angular.module('chalicepoints.controllers', [])

  .controller('AppController', ['$scope', '$modal', 'flash', 'User',
    function($scope, $modal, flash, User) {
      $scope.openUserSettings = function() {
        var modal = $modal.open({
          templateUrl: '/public/partials/modals/user_settings.html',
          controller: 'UserSettingsModalController',
          windowClass: 'small',
          resolve: {
            user: function() {
              return $scope.current_user;
            }
          }
        });

        modal.result.then(function(user) {
          $scope.current_user = user;
          User.update(user);
        });
      };
    }
  ])

  .controller('LeaderboardController', ['$scope', 'flash', 'User', 'Leaderboard', 'CPEvent', 'Types', 'TypeGroups',
    function($scope, flash, User, Leaderboard, CPEvent, Types, TypeGroups) {
      $scope.types = Types;
      $scope.typeGroups = TypeGroups;

      $scope.selected = {
        week: true,
        month: false,
        all: false
      };

      $scope.leaderboard = {
        week: {
          given: [],
          received: []
        },
        month: {
          given: [],
          received: []
        },
        all: {
          given: [],
          received: []
        }
      };

      $scope.users = [];

      $scope.pointsAmount = 1;

      $scope.loading = {
        leaderboard: {
          week: true,
          month: true,
          all: true
        },
        targets: true
      };

      Leaderboard.get({
        type: 'week'
      }, function(result) {
        if (!result || !result.success || !result.given || !result.received) {
          // Error
          return;
        }

        $scope.leaderboard.week = result;
        $scope.loading.leaderboard.week = false;
      }, function(result) {
        $scope.loading.leaderboard.week = false;
      });

      Leaderboard.get({
        type: 'month'
      }, function(result) {
        if (!result || !result.success || !result.given || !result.received) {
          // Error
          return;
        }

        $scope.leaderboard.month = result;
        $scope.loading.leaderboard.month = false;
      }, function(result) {
        $scope.loading.leaderboard.month = false;
      });

      Leaderboard.get({
        type: 'all'
      }, function(result) {
        if (!result || !result.success || !result.given || !result.received) {
          // Error
          return;
        }

        $scope.leaderboard.all = result;
        $scope.loading.leaderboard.all = false;
      }, function(result) {
        $scope.loading.leaderboard.all = false;
      });

      User.targets({}, function(results) {
        for (var i = results.length - 1; i >= 0; i--) {
          if (results[i].disabled) {
            results.splice(i, 1);
          }
        }

        $scope.users = results;
        $scope.loading.targets = false;
      }, function(result) {
        $scope.loading.targets = false;
      });

      $scope.select = function(type) {
        for (var selectedType in $scope.selected) {
          $scope.selected[selectedType] = false;
        }

        $scope.selected[type] = true;
      };

      $scope.addEvent = function() {
        if ($scope.pointsTarget == $scope.current_user.name) {
          flash('alert', "Really? You can't give yourself points.");
          return;
        }

        $scope.pointsAmount = Math.max(Math.min($scope.current_user.max_points, $scope.pointsAmount), 1);

        var cpEvent = new CPEvent({
          target: $scope.pointsTarget,
          amount: $scope.pointsAmount,
          message: $scope.pointsMessage,
          type: $scope.pointsType
        });

        cpEvent.$save(function(data) {
          flash('success', 'Chalice Point Given');

          $scope.pointsAmount = 1;
          $scope.pointsTarget = '';
          $scope.pointsMessage = '';
          $scope.pointsType = '';

          var weekResult = Leaderboard.get({
            type: 'week'
          }, function() {
            $scope.leaderboard.week = weekResult;
          });

          var monthResult = Leaderboard.get({
            type: 'month'
          }, function() {
            $scope.leaderboard.month = monthResult;
          });

          var allResult = Leaderboard.get({
            type: 'all'
          }, function() {
            $scope.leaderboard.all = allResult;
          });
        });
      };
    }
  ])

  .controller('HistoryController', ['$scope', '$location', 'History', 'Types',
    function($scope, $location, History, Types) {
      var loadHistory = function(type) {
        History.load(type, $scope.params).then(function(result) {
          if (!result || !result.history || !('count' in result)) {
            // Error
            return false;
          }

          $scope.history[type] = result.history;
          $scope.pages[type].total = Math.ceil(result.count / $scope.params[type].limit);

          if ($scope.pages[type].total <= 5) {
            $scope.pages[type].start = 2;
            $scope.pages[type].end = $scope.pages[type].total - 1;
          } else {
            $scope.pages[type].start = Math.max(2, $scope.params[type].page - 1);
            $scope.pages[type].end = Math.min($scope.pages[type].total - 1, $scope.params[type].page + 1);
          }
        });
      };

      $scope.history = {
        all: [],
        source: [],
        target: [],
        type: []
      };

      $scope.pages = {
        all: {
          total: 1,
          start: 1,
          end: 1
        },
        source: {
          total: 1,
          start: 1,
          end: 1
        },
        target: {
          total: 1,
          start: 1,
          end: 1
        },
        type: {
          total: 1,
          start: 1,
          end: 1
        }
      };

      $scope.selected = {
        all: true,
        source: false,
        target: false,
        type: false
      };

      $scope.select = function(type) {
        for (var ctype in $scope.selected) {
          $scope.selected[ctype] = false;
        }

        $scope.selected[type] = true;
      };

      $scope.range = function(start, end, step) {
        if (typeof end == 'undefined') {
          end = start;
          start = 1;
        }

        step = typeof step == 'undefined' ? 1 : step;

        var result = [];

        for (var i = start; i <= end; i += step) {
          result.push(i);
        }

        return result;
      };

      $scope.types = Types;

      var minDate = moment().startOf('month');
      var maxDate = moment().endOf('month');

      $scope.params = {
        common: {
          minDate: minDate.format('YYYY-MM-DD'),
          maxDate: maxDate.format('YYYY-MM-DD'),
          filters: {
            other: '0'
          }
        },
        all: {
          sort: {
            direction: 'DESC',
            field: 'created_at'
          },
          page: 1,
          limit: 10
        },
        source: {
          page: 1,
          limit: 10
        },
        target: {
          page: 1,
          limit: 10
        },
        type: {
          page: 1,
          limit: 10
        }
      };

      var search = $location.search();
      search.filters = {};

      for (var filter in $scope.params.common.filters) {
        var filterString = 'filters[' + filter + ']';
        if (filterString in search) {
          search.filters[filter] = search[filterString];
          delete search[filterString];
        }
      }

      $scope.params.common = $.extend({}, $scope.params.common, search);
          
      loadHistory('all');
      loadHistory('source');
      loadHistory('target');
      loadHistory('type');

      $scope.$watch('params.common', function(newVal, oldVal) {
        if (newVal === oldVal) {
          return;
        }

        if (!newVal) {
          return;
        }

        for (var type in $scope.history) {
          $scope.params[type].page = 1;
          loadHistory(type);
        }

        var query = $.param($scope.params.common);
        $location.search(query);
      }, true);

      $scope.prevPage = function(type) {
        if ($scope.params[type].page == 1) {
          return;
        }

        $scope.params[type].page--;
        loadHistory(type);
      };

      $scope.nextPage = function(type) {
        if ($scope.params[type].page == $scope.pages[type].total) {
          return;
        }

        $scope.params[type].page++;
        loadHistory(type);
      };

      $scope.goToPage = function(type, page) {
        if (page < 1 || page > $scope.pages[type]) {
          return;
        }

        $scope.params[type].page = page;
        loadHistory(type);
      };

      $scope.toggleSort = function(type, field) {
        if ($scope.params[type].sort.field == field) {
          $scope.params[type].sort.direction = $scope.params[type].sort.direction == 'ASC' ? 'DESC' : 'ASC';
        } else {
          $scope.params[type].sort.field = field;
          $scope.params[type].sort.direction = 'ASC';
        }

        loadHistory(type);
      };
    }
  ])

  .controller('UserController', ['$scope', '$routeParams', '$modal', 'CPEvent', 'User', 'Types',
    function($scope, $routeParams, $modal, CPEvent, User, Types) {
      $scope.loading = {
        user: true,
        events: true
      };

      $scope.types = Types;

      User.get({
        id: $routeParams.id
      }, function(result) {
        $scope.user = result;
        $scope.loading.user = false;
      }, function(result) {
        $scope.loading.user = false;
      });

      User.timeline({
        id: $routeParams.id
      }, function(result) {
        $scope.events = result;

        for (var i = 0, length = $scope.events.length; i < length; i++) {
          if ($scope.events[i].target.id == $scope.current_user.id) {
            $scope.events[i].direction = 'receive';
          } else {
            $scope.events[i].direction = 'give';
          }
        }

        $scope.loading.events = false;
      }, function(result) {
        $scope.loading.events = false;
      });

      $scope.predicate = 'name';
      $scope.reverse = false;

      $scope.editEvent = function(idx) {
        $scope.event = $scope.events[idx];

        var modal = $modal.open({
          templateUrl: '/public/partials/modals/edit_event.html',
          controller: 'EditEventModalController',
          windowClass: 'small',
          resolve: {
            event: function() {
              return $scope.event;
            },
            users: function($q, User) {
              var deferred = $q.defer();
              var res = User.targets(function() {
                for (var i = res.length - 1; i >= 0; i--) {
                }

                deferred.resolve(res);
              });
              return deferred.promise;
            }
          }
        });

        modal.result.then(function(evt) {
          CPEvent.update(null, evt);
        });
      };

      $scope.removeEvent = function(id) {
        if (!confirm('Are you sure you want to delete this event?')) {
          return false;
        }

        CPEvent.delete({}, {'id': id}, function(data) {
          $scope.loading.events = true;

          User.timeline({
            id: $scope.user.id
          }, function(result) {
            $scope.events = result;
            $scope.loading.events = false;
          }, function(result) {
            $scope.loading.events = false;
          });
        });
      };
    }
  ])

  .controller('ElderUsersController', ['$scope', '$routeParams', '$modal', 'User',
    function($scope, $routeParams, $modal, User) {
      $scope.predicate = 'name';
      $scope.reverse = false;

      User.query({}, function(results) {
        $scope.users = results;
      });

      $scope.user = null;

      $scope.editUser = function(user) {
        $scope.user = user;

        var modal = $modal.open({
          templateUrl: '/public/partials/modals/edit_user.html',
          controller: 'EditUserModalController',
          windowClass: 'tiny',
          resolve: {
            user: function() {
              return $scope.user;
            }
          }
        });

        modal.result.then(function(user) {
          User.update(null, user);
        });
      };

      $scope.removeUser = function(user) {
        if (!confirm('Are you sure you want to delete this user?')) {
          return false;
        }

        User.delete({}, user, function(data) {
          for (var i = 0; i < $scope.users.length; i++) {
            if ($scope.users[i].id == user.id) {
              $scope.users.splice(i, 1);
              break;
            }
          }
        });
      };

      $scope.mergeUser = function(user) {
        $scope.user = user;

        var modal = $modal.open({
          templateUrl: '/public/partials/modals/merge_user.html',
          controller: 'MergeUserModalController',
          windowClass: 'tiny',
          resolve: {
            user: function() {
              return $scope.user;
            },
            users: function() {
              return $scope.users;
            }
          }
        });

        modal.result.then(function(merge) {
          User.merge(merge, function() {
            for (var i = 0; i < $scope.users.length; i++) {
              if ($scope.users[i].id == user.id) {
                $scope.users.splice(i, 1);
                break;
              }
            }
          });
        });
      };
    }
  ])

  .controller('EditUserModalController', ['$scope', '$modalInstance', 'user',
    function($scope, $modalInstance, user) {
      $scope.user = user;

      $scope.ok = function() {
        $modalInstance.close($scope.user);
      };

      $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
      };
    }
  ])

  .controller('EditEventModalController', ['$scope', '$modalInstance', 'event', 'users',
    function($scope, $modalInstance, event, users) {
      $scope.event = event;
      $scope.users = users;

      $scope.ok = function() {
        $modalInstance.close($scope.event);
      };

      $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
      };
    }
  ])

  .controller('MergeUserModalController', ['$scope', '$modalInstance', 'user', 'users',
    function($scope, $modalInstance, user, users) {
      $scope.user = user;
      $scope.users = angular.copy(users);
      $scope.merge = {
        id: $scope.user.id,
        target: null
      };

      for (var i = $scope.users.length - 1; i >= 0; i--) {
        if ($scope.users[i].id == $scope.user.id) {
          $scope.users.splice(i, 1);
          break;
        }
      }

      $scope.ok = function() {
        $modalInstance.close($scope.merge);
      };

      $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
      };
    }
  ])

  .controller('UserSettingsModalController', ['$scope', '$modalInstance', 'user',
    function($scope, $modalInstance, user) {
      $scope.user = user;

      if (!('settings' in $scope.user)) {
        $scope.user.settings = {};
      }

      if (!('email' in $scope.user.settings)) {
        $scope.user.settings.email = {};
      }

      $scope.ok = function() {
        $modalInstance.close($scope.user);
      };

      $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
      };
    }
  ]);
})();
