// rot_banyan.v -- Banyan (butterfly) circular left rotator, N = 2^n (chapter 06)
//
//   dout lane i = din lane (i + shift) mod N
//
// n stages of N/2 2x2 switches. At stage d the bus is cut into blocks of
// B = N >> d lanes; inside each block, switch k joins lane k with lane k + H
// (H = B/2). Control for stage d (derivation in chapter 06):
//
//   a     = shift[n-1-d]              one bit: swap the two halves?
//   b     = shift mod H               the low bits: no modulo hardware
//   swap  = a XOR (k < b)             (k < b) is a thermometer code of b
//
// Every block in stage d uses the SAME control vector, so control costs one
// thermometer decoder per stage, shared by all 2^d sub-networks.
//
// Datapath cost is identical to rot_barrel (N*log2 N 2:1 muxes). What the
// Banyan buys is structure: forcing the first f stages to "bar" splits it
// into 2^f independent rotators (multi-frame mode, chapter 06 exercise).
module rot_banyan #(
    parameter N  = 8,                // must be a power of two, >= 2
    parameter W  = 8,
    parameter SW = $clog2(N)
) (
    input  wire [N*W-1:0] din,
    input  wire [SW-1:0]  shift,
    output wire [N*W-1:0] dout
);
    wire [N*W-1:0] stage [0:SW];
    assign stage[0] = din;

    genvar d, j, k;
    generate
        for (d = 0; d < SW; d = d + 1) begin : g_stage
            localparam B = N >> d;          // block size at this stage
            localparam H = B >> 1;          // half block = switch span
            localparam [SW-1:0] MASK = {SW{1'b1}} >> (d + 1);   // = H - 1

            // ---- control generation: shared by every block in this stage
            wire          a = shift[SW-1-d];
            wire [SW-1:0] b = shift & MASK;
            wire [H-1:0]  swap;
            for (k = 0; k < H; k = k + 1) begin : g_ctl
                assign swap[k] = a ^ (k < b);
            end

            // ---- datapath: N/2 2x2 switches
            for (j = 0; j < N / B; j = j + 1) begin : g_blk
                for (k = 0; k < H; k = k + 1) begin : g_sw
                    localparam U = j * B + k;   // upper input/output lane
                    localparam L = U + H;       // lower input/output lane
                    sw2 #(.W(W)) u_sw (
                        .in0  (stage[d][U*W +: W]),
                        .in1  (stage[d][L*W +: W]),
                        .swap (swap[k]),
                        .out0 (stage[d+1][U*W +: W]),
                        .out1 (stage[d+1][L*W +: W])
                    );
                end
            end
        end
    endgenerate

    assign dout = stage[SW];
endmodule
