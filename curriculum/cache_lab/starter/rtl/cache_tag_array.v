module cache_tag_array(
  input         clk,
  input         reset,
  input  [1:0]  read_index,
  output [3:0]  read_tag,
  output        read_valid,
  input         write_enable,
  input  [1:0]  write_index,
  input  [3:0]  write_tag
);
  reg [3:0] tags [0:3];
  reg valid [0:3];
  integer i;

  // TODO: reset and write the tag/valid arrays on the clock edge.
  always @(posedge clk) begin
    if (reset) begin
      for (i = 0; i < 4; i = i + 1) begin
        tags[i] <= 4'b0;
        valid[i] <= 1'b0;
      end
    end
  end

  assign read_tag = tags[read_index];
  assign read_valid = valid[read_index];
endmodule
