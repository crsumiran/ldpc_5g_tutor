// rot_ibn3.v -- Improved Banyan Network rotator, N = 3 * 2^n (chapter 06)
//
//   dout lane i = din lane (i + shift) mod N,   0 <= shift < N
//
// Idea from Song, Cui, Wang, "A Universal Efficient Circular-Shift Network
// for Reconfigurable QC-LDPC Decoders", IEEE TVLSI 30(10), 2022.
//
// Put the 3x3 stage FIRST, then three power-of-two Banyans of M = 2^n lanes.
// With M a power of two, splitting the shift is free bit slicing:
//
//   a = shift[n+1:n]   (0, 1 or 2: how many whole blocks to rotate)
//   b = shift[n-1:0]   (rotation inside each block)
//
//   3x3 switch k (lanes k, k+M, k+2M) rotates the blocks by  a + (k < b)  mod 3
//   then all three Banyans rotate left by b
//
// The older VBN puts the 3x3 stage last, so its sub-networks have 3*2^j
// lanes and every stage needs  shift mod (3*2^j)  -- real modulo hardware.
// Moving the stage first removes every modulo. That is the paper's key trick.
module rot_ibn3 #(
    parameter M  = 128,              // block size, power of two (N = 3*M)
    parameter W  = 8,
    parameter N  = 3 * M,
    parameter SW = $clog2(N),
    parameter MW = $clog2(M)
) (
    input  wire [N*W-1:0] din,
    input  wire [SW-1:0]  shift,
    output wire [N*W-1:0] dout
);
    wire [1:0]    a = shift[SW-1:MW];     // shift < 3M, so a is 0..2
    wire [MW-1:0] b = shift[MW-1:0];

    wire [N*W-1:0] mid;                   // after the 3x3 stage

    genvar k;
    generate
        for (k = 0; k < M; k = k + 1) begin : g_sw3
            // a + (k < b), reduced mod 3; a <= 2 so the sum is at most 3
            wire [1:0] sum = a + (k < b);
            wire [1:0] r   = (sum == 2'd3) ? 2'd0 : sum;
            sw3 #(.W(W)) u_sw (
                .in0 (din[(k      )*W +: W]),
                .in1 (din[(k +   M)*W +: W]),
                .in2 (din[(k + 2*M)*W +: W]),
                .r   (r),
                .out0(mid[(k      )*W +: W]),
                .out1(mid[(k +   M)*W +: W]),
                .out2(mid[(k + 2*M)*W +: W])
            );
        end
    endgenerate

    rot_banyan #(.N(M), .W(W)) u_b0 (.din(mid[0*M*W +: M*W]), .shift(b), .dout(dout[0*M*W +: M*W]));
    rot_banyan #(.N(M), .W(W)) u_b1 (.din(mid[1*M*W +: M*W]), .shift(b), .dout(dout[1*M*W +: M*W]));
    rot_banyan #(.N(M), .W(W)) u_b2 (.din(mid[2*M*W +: M*W]), .shift(b), .dout(dout[2*M*W +: M*W]));
endmodule
