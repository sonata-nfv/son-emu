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
    .size([width, height]);

//d3.json("js/graph.json", function(error, json) {
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
      .call(force.drag)
      .on("click", click);

  //node.append("image")
  //    .attr("xlink:href", "https://github.com/favicon.ico")
  //    .attr("x", -8)
  //    .attr("y", -8)
  //    .attr("width", 16)
  //    .attr("height", 16);
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

  // action to take on mouse click
  function click() {
      d3.select(this).select("text").transition()
          .duration(750)
          .attr("x", 22)
          .style("stroke", "lightsteelblue")
          .style("stroke-width", ".5px")
          .style("font", "20px sans-serif");
      d3.select(this).select("circle").transition()
          .duration(750)
          .attr("r", 16);
  }

});