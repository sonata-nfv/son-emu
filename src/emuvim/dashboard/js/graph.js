// action to take on double mouse click, call rest api to start xterm
  function dblclick() {
      var vnf_name = d3.select(this).text()
      console.debug(vnf_name)
      var rest_url = "http://127.0.0.1:5001/restapi/monitor/term?vnf_list=" + vnf_name

      d3.json(rest_url, function(error, json) {
        if (error) throw error;
        console.debug(json)
      });
  }

  //functions to make the nodes stick after they have been manually maoved
  function tick() {
    link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });
  }

  function dragstart(d) {
     d3.select(this).classed("fixed", d.fixed = true);
  }

var width = 960,
    height = 500,
    color = d3.scale.category10();

var svg = d3.select("#table_graph").append("svg")
    .attr("width", width)
    .attr("height", height);

var force = d3.layout.force()
    .gravity(0.05)
    .distance(100)
    .charge(-100)
    .size([width, height])
    .on("tick", tick);

var drag = force.drag()
    .on("dragstart", dragstart);

d3.json("http://127.0.0.1:5001/restapi/network/d3jsgraph", function(error, json) {
  if (error) throw error;

  force
      .nodes(json.nodes)
      .links(json.links)
      .start();

  var link = svg.selectAll(".link")
      .data(json.links)
      .enter().append("line")
      .attr("class", "link");

  var node = svg.selectAll(".node")
      .data(json.nodes)
      .enter().append("g")
      .attr("class", "node")
      .on("dblclick", dblclick)
      .call(drag);

  node.append("circle")
    .attr("r", 10)
    .style("fill", function(d) { return color(d.group); });

  node.append("text")
      .attr("dx", 12)
      .attr("dy", ".35em")
      .text(function(d) { return d.name });

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
  });

  


});
