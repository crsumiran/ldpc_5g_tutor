module cache_address_decode(
  input  [7:0] addr,
  output [3:0] tag,
  output [1:0] index,
  output [1:0] byte_offset
);
  assign tag = addr[7:4];
  assign index = addr[3:2];
  assign byte_offset = addr[1:0];
endmodule
