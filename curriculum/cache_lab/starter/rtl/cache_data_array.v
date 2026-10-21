module cache_data_array(
  input         clk,
  input         reset,
  input  [1:0]  read_index,
  output [31:0] read_data,
  input         write_enable,
  input  [1:0]  write_index,
  input  [31:0] write_data
);
  reg [31:0] data [0:3];
  integer i;

  // TODO: implement the four-word storage array.
  always @(posedge clk) begin
    if (reset) begin
      for (i = 0; i < 4; i = i + 1)
        data[i] <= 32'b0;
    end
  end

  assign read_data = data[read_index];
endmodule
