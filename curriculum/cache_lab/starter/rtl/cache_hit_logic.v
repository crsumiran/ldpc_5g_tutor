module cache_hit_logic(
  input  [3:0] req_tag,
  input  [3:0] line_tag,
  input        line_valid,
  output       hit
);
  // TODO: a hit requires both a valid line and a matching tag.
  assign hit = 1'b0;
endmodule
