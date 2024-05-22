// 设置SVG画布的尺寸
const width = 800;
const height = 600;
const margin = { top: 40, right: 50, bottom: 40, left: 40 };  // 增加边距定义

// 创建SVG元素
const svg = d3.select('body').append('svg')
    .attr('width', width)
    .attr('height', height);

svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '-0 -5 10 10')
    .attr('refX', 5)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('xoverflow', 'visible')
    .append('svg:path')
    .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
    .attr('fill', '#999');

// 加载数据
Promise.all([
    d3.csv('data.csv'),
    d3.csv('links.csv')]).then(files => {

    const nodes = files[0];
    const links = files[1];

    // 定义比例尺，考虑边距
    const xScale = d3.scaleLinear()
        .domain([d3.min(nodes, d => +d.X), d3.max(nodes, d => +d.X)])
        .range([margin.left, width - margin.right]);  // 考虑左右边距

    const yScale = d3.scaleLinear()
        .domain([d3.min(nodes, d => +d.Y), d3.max(nodes, d => +d.Y)])
        .range([height - margin.bottom, margin.top]);  // 考虑上下边距

    // 定义颜色比例尺 - 针对离散数据
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
        .domain(nodes.map(d => d.Strength))

    const sizeScale = d3.scaleLinear()
        .domain([d3.min(nodes, d => d.local_citation ? +d.local_citation : 0), d3.max(nodes, d => d.local_citation ? +d.local_citation : 0)])
        .range([20, 50]);  // 调整大小范围以适应您的视觉需求

    const shapeScale = d3.scaleOrdinal()
        .domain(["B", "Mg", "Zn", "H"])  // 根据您的数据具体类型调整
        .range([d3.symbolCircle, d3.symbolSquare, d3.symbolTriangle, d3.symbolDiamond]);  // 根据您的需要选择形状

    // 先绘制箭头（这样点会在箭头上面）
    svg.selectAll('.link')
        .data(links)
        .enter().append('line')
        .attr('class', 'link')
        .attr('x1', d => xScale(nodes[d.s].X))
        .attr('y1', d => yScale(nodes[d.s].Y))
        .attr('x2', d => xScale(nodes[d.t].X))
        .attr('y2', d => yScale(nodes[d.t].Y))
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.4) // 设置透明度
        .attr('marker-end', 'url(#arrowhead)');

    // 绘制点
    svg.selectAll('.dot')
        .data(nodes)
        .enter().append('path')
        .classed('dot', true)
        .attr('transform', d => `translate(${xScale(d.X)}, ${yScale(d.Y)})`)
        .attr('d', d => d3.symbol()
        .size(d.local_citation ? sizeScale(d.local_citation) ** 2 : 100)
        .type(shapeScale(d['Reaction Type']))())
        .style('fill', d => colorScale(d.Strength));  // 使用颜色比例尺设置填充颜色

    svg.selectAll('.label')
        .data(nodes)
        .enter().append('text')
        .attr('class', 'label')
        .attr('x', d => xScale(d.X))
        .attr('y', d => yScale(d.Y) - 15)  // 调整位置，使标签位于节点上方
        .attr('text-anchor', 'middle')  // 文本居中对齐
        .style('font-size', '8px')  // 设置字体大小为12px
        .text(d => d.last_author_publication_year);  // 显示 publication year
    

        // 添加图例
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(" + (width - 150) + ", 30)");
  
    colorScale.domain().forEach((d, i) => {
        legend.append("circle")
          .attr("r", 5)
          .attr("cx", 0)
          .attr("cy", i * 20)
          .style("fill", colorScale(d));
  
        legend.append("text")
          .attr("x", 10)
          .attr("y", i * 20+0.5)
          .text(d)
          .style("font-size", "12px")
          .attr("alignment-baseline", "middle");
      });

    // 添加形状图例
    const shapeLegend = svg.append("g")
        .attr("class", "legend shape-legend")
        .attr("transform", "translate(" + (width - 150) + ", 80)");

    shapeScale.domain().forEach((d, i) => {
        shapeLegend.append("path")
        .attr('d', d3.symbol().type(shapeScale(d)).size(64))
        .attr("transform", `translate(0, ${i * 30+13})`)
        .style("fill", "grey");

        shapeLegend.append("text")
        .attr("x", 20)
        .attr("y", i * 30 + 15)
        .text(d)
        .style("font-size", "12px")
        .attr("alignment-baseline", "middle");
    });

}).catch(e => {
    console.error('Error loading the data: ', e);
});
