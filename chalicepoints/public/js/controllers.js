'use strict';

var LeaderboardCtrl = ['$scope', 'flash', 'users', 'leaderboardWeek', 'leaderboardMonth', 'leaderboardAll', 'CPEvent', 'Leaderboard', 'Types', 'TypeOrder',
  function($scope, flash, users, leaderboardWeek, leaderboardMonth, leaderboardAll, CPEvent, Leaderboard, Types, TypeOrder) {

  $scope.leaderboard = {
    week: leaderboardWeek,
    month: leaderboardMonth,
    all: leaderboardAll
  };

  $scope.users = users;

  $scope.types = Types;
  $scope.typeOrder = TypeOrder;

  $scope.selected = {
    week: true,
    month: false,
    all: false
  };

  $scope.select = function(type) {
    for (var ctype in $scope.selected) {
      $scope.selected[ctype] = false;
    }

    $scope.selected[type] = true;
  };

  $scope.pointsAmount = 1;

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
}];

LeaderboardCtrl.resolve = {
  leaderboardWeek: function($q, Leaderboard) {
    var deferred = $q.defer();
    var res = Leaderboard.get({
      type: 'week'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  },
  leaderboardMonth: function($q, Leaderboard) {
    var deferred = $q.defer();
    var res = Leaderboard.get({
      type: 'month'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  },
  leaderboardAll: function($q, Leaderboard) {
    var deferred = $q.defer();
    var res = Leaderboard.get({
      type: 'all'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  },
  users: function($q, User) {
    var deferred = $q.defer();
    var res = User.query(function() {
      for (var i = res.length - 1; i >= 0; i--) {
        if (res[i].disabled) {
          res.splice(i, 1);
        }
      }

      deferred.resolve(res);
    });
    return deferred.promise;
  }
};

var HistoryCtrl = ['$scope', 'History', 'Types', function($scope, History, Types) {
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

    console.log(start, end, step, result);

    return result;
  };

  $scope.types = Types;

  var minDate = moment().startOf('month');
  var maxDate = moment().endOf('month');

  $scope.params = {
    common: {
      minDate: minDate.format('YYYY-MM-DD'),
      maxDate: maxDate.format('YYYY-MM-DD'),
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
}];

var TimelineCtrl = ['$scope', 'timeline', function($scope, timeline) {
  $scope.timeline = timeline;
}];

TimelineCtrl.resolve = {
  timeline: function($q, Timeline, $route) {
    var deferred = $q.defer();
    var res = Timeline.query(function() {
      deferred.resolve(res);
    });

    return deferred.promise;
  }
};

var UserCtrl = ['$scope', '$routeParams', 'CPEvent', 'User', 'user', '$modal',
  function($scope, $routeParams, CPEvent, User, user, $modal) {
  $scope.user = user;

  $scope.predicate = 'name';
  $scope.reverse = false;

  $scope.editEvent = function(idx) {
    $scope.event = $scope.user.events[idx];

    var modal = $modal.open({
      templateUrl: '/public/partials/modals/edit_event.html',
      controller: EditEventModalCtrl,
      windowClass: 'small',
      resolve: {
        event: function() {
          return $scope.event;
        },
        users: function($q, User) {
          var deferred = $q.defer();
          var res = User.query(function() {
            for (var i = res.length - 1; i >= 0; i--) {
              if (res[i].disabled) {
                res.splice(i, 1);
              }
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
      $scope.user = User.get({
        id: $scope.user.id
      });
    });
  };
}];

UserCtrl.resolve = {
  user: function($q, User, $route) {
    var deferred = $q.defer();
    var res = User.get({
      id: $route.current.params.id
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  }
};

var ElderUsersCtrl = ['$scope', '$routeParams', 'User', 'users', '$modal',
  function($scope, $routeParams, User, users, $modal) {
    $scope.users = users;
    $scope.user = null;

    $scope.editUser = function(user) {
      $scope.user = user;

      var modal = $modal.open({
        templateUrl: '/public/partials/modals/edit_user.html',
        controller: EditUserModalCtrl,
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
        controller: MergeUserModalCtrl,
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
}];

ElderUsersCtrl.resolve = {
  users: function($q, User, $route) {
    var deferred = $q.defer();
    var res = User.query({
      id: 'all'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  }
};

var EditUserModalCtrl = ['$scope', '$modalInstance', 'user', function($scope, $modalInstance, user) {
  $scope.user = user;

  $scope.ok = function() {
    $modalInstance.close($scope.user);
  };

  $scope.cancel = function() {
    $modalInstance.dismiss('cancel');
  };
}];

var EditEventModalCtrl = ['$scope', '$modalInstance', 'event', 'users', function($scope, $modalInstance, event, users) {
  $scope.event = event;
  $scope.users = users;

  $scope.ok = function() {
    $modalInstance.close($scope.event);
  };

  $scope.cancel = function() {
    $modalInstance.dismiss('cancel');
  };
}];

var MergeUserModalCtrl = ['$scope', '$modalInstance', 'user', 'users', function($scope, $modalInstance, user, users) {
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
}];
