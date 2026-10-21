module cache_address_decode(
  input  [7:0] addr,
  output [3:0] tag,
  output [1:0] index,
  output [1:0] byte_offset
);
  // TODO: connect each output to the correct address field.
  assign tag = 4'b0;
  assign index = 2'b0;
  assign byte_offset = 2'b0;
endmodule
