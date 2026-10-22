// switches.v -- the two switch primitives used in this tutorial (chapter 03)

// 2x2 switch. bar (straight): out0=in0, out1=in1.  swap: out0=in1, out1=in0.
// It is nothing more than two 2:1 muxes sharing one select line.
module sw2 #(parameter W = 8) (
    input  wire [W-1:0] in0, in1,
    input  wire         swap,
    output wire [W-1:0] out0, out1
);
    assign out0 = swap ? in1 : in0;
    assign out1 = swap ? in0 : in1;
endmodule

// 3x3 rotating switch: out[q] = in[(q + r) mod 3], r in {0,1,2}.
// Three 3:1 muxes. Only the 3 cyclic orders are needed, not all 6 permutations.
module sw3 #(parameter W = 8) (
    input  wire [W-1:0] in0, in1, in2,
    input  wire [1:0]   r,
    output reg  [W-1:0] out0, out1, out2
);
    always @* begin
        case (r)
            2'd1:    begin out0 = in1; out1 = in2; out2 = in0; end
            2'd2:    begin out0 = in2; out1 = in0; out2 = in1; end
            default: begin out0 = in0; out1 = in1; out2 = in2; end
        endcase
    end
endmodule
