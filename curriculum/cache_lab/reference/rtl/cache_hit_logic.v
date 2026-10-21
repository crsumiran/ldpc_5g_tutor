module cache_hit_logic(
  input  [3:0] req_tag,
  input  [3:0] line_tag,
  input        line_valid,
  output       hit
);
  assign hit = line_valid && (req_tag == line_tag);
endmodule
