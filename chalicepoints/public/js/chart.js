'use strict';

var ChalicePoints = {
    type: 'received'
};

ChalicePoints.Chord = function(type) {
    ChalicePoints.type = type || 'received';

    var elem = document.getElementById('chart');
    if (!elem) {
        return false;
    }

    elem.innerHTML = '';

    var width = 650;
    var height = 650;
    var outerRadius = Math.min(width, height) / 2;
    var innerRadius = outerRadius - 45;

    var arc = d3.svg.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);

    var layout = d3.layout.chord()
        .padding(0.04)
        .sortSubgroups(d3.descending)
        .sortChords(d3.ascending);

    var path = d3.svg.chord()
        .radius(innerRadius);

    var svg = d3.select('#chart').append('svg')
        .attr('width', width)
        .attr('height', height)
    .append('g')
        .attr('id', 'circle')
        .attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');

    svg.append('circle')
        .attr('r', outerRadius);

    var colors = d3.scale.category20();

    d3.json('/api/1.0/user', function(users) {
        d3.json('/api/1.0/matrix/' + ChalicePoints.type, function(matrix) {
            layout.matrix(matrix);

            var group = svg.selectAll('.group')
                .data(layout.groups)
            .enter().append('g')
                .attr('class', 'group')
                .attr('title', function(d, i) {
                    var title = 'Unknown';
                    if (users[i]) {
                        title = users[i].name + ': ' + Math.round(d.value);
                    }
                    
                    return title;
                })
                .on('mouseover', mouseover);

            group.append('title').text(function(d, i) {
                var title = 'Unknown';
                if (users[i]) {
                    title = users[i].name + ': ' + Math.round(d.value);
                }

                return title;
            });

            var groupPath = group.append('path')
                .attr('id', function(d, i) {
                    return 'group' + i;
                })
                .attr('d', arc)
                .style('fill', function(d, i) {
                    return colors(i);
                });

            var groupText = group.append('text')
                .attr('x', 10)
                .attr('dy', 20);

            groupText.append('textPath')
                .attr('xlink:href', function(d, i) {
                    return '#group' + i;
                })
                .text(function(d, i) {
                    var text = 'Unknown';
                    if (users[i]) {
                        text = users[i].name;
                    }

                    return text;
                });

            groupText.filter(function(d, i) {
                return groupPath[0][i].getTotalLength() / 2 - 10 < this.getComputedTextLength();
            }).remove();

            var chord = svg.selectAll('.chord')
                .data(layout.chords)
            .enter().append('path')
                .attr('class', 'chord')
                .style('fill', function(d) {
                    return colors(d.source.index);
                })
                .attr('d', path);

            chord.append('title').text(function(d) {
                var tooltip = 'Unknown';
                if (ChalicePoints.type == 'received') {
                    if (users[d.source.index] && users[d.target.index]) {
                        tooltip = users[d.source.index].name +
                            ' -> ' + users[d.target.index].name +
                            ': ' + d.target.value +
                            "\n" +
                            users[d.target.index].name +
                            ' -> ' + users[d.source.index].name +
                            ': ' + d.source.value;
                    }
                } else {
                    if (users[d.source.index] && users[d.target.index]) {
                        tooltip = users[d.target.index].name +
                            ' -> ' + users[d.source.index].name +
                            ': ' + d.target.value +
                            "\n" +
                            users[d.source.index].name +
                            ' -> ' + users[d.target.index].name +
                            ': ' + d.source.value;
                    }
                }

                return tooltip;
            });

            function mouseover(d, i) {
                chord.classed('fade', function(p) {
                    return p.source.index != i && p.target.index != i;
                });
            }
        });
    });
};

function matrixChoice(type) {
    ChalicePoints.Chord(type);
}
