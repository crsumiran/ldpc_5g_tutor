export type Checkpoint = {
  id: string;
  title: string;
  goal: string;
  description: string;
  requirements: string[];
  module: string;
  prerequisites: string[];
  source_files: string[];
  editable_files: string[];
  public_testbench: string;
  hidden_testbench: string;
  top: string;
  hidden_top?: string | null;
  estimated_minutes: number;
  difficulty: "easy" | "medium" | "hard";
  concepts: string[];
  hints: string[];
  trace_signals: string[];
  compile_testbench?: string | null;
  lesson?: string;
  input_reference?: string;
  visual?: string;
  prediction?: string;
  reflection?: string;
  fixture?: TeachingFixture;
  experiment?: string;
  optional_math?: string;
  optional_hardware?: string;
  takeaway?: string;
  completion?: string;
  misconception?: string;
};

export type TeachingView = { title: string; columns: string[]; rows: (string | number | boolean)[][]; caption: string };
export type TeachingFixture = { id: string; label: string; kind?: string; matrix?: number[][]; edges?: {id: string; check: number; bit: number}[]; views: TeachingView[]; variants?: {label: string; views: TeachingView[]}[]; visual_spec: {labels: string[]; view_type: string; selected_element: string; step_sequence: string[]; expected_observation: string; caption: string; text_fallback: string; data_origin: string} };

export type CheckpointProgress = {
  id: string;
  title: string;
  goal: string;
  status: "locked" | "available" | "in_progress" | "passed";
  estimated_minutes: number;
  difficulty: string;
  concepts: string[];
};

export type OpticalVisualId = "correspondence" | "patch" | "ambiguity" | "sampling" | "alignment" | "refinement" | "pyramid" | "evaluation" | "consistency";
export type TheorySection = {title: string; text: string; visual?: OpticalVisualId | null};
export type TheoryPage = {
  fixture?: TeachingFixture;
  id: string; title: string; goal: string;
  diagram: "channel" | "repetition" | "parity" | "graph" | "decoding" | "hardware" | "flow";
  sections: TheorySection[];
  optional_sections?: TheorySection[];
  question: string; answer: string;
  connections: {id: string; why: string}[];
};

export type CourseResponse = {
  manifest: {
    id: string;
    title: string;
    subtitle: string;
    toolchain?: "iverilog" | "python";
    checkpoints: Checkpoint[];
    provided_files: string[];
  };
  overview: string;
  architecture: string;
  theory_pages?: TheoryPage[];
  session_id?: string | null;
  progress: CheckpointProgress[];
};

export type LabSession = {
  id: string;
  course_id: string;
  learner_key: string;
  passed_checkpoint_ids: string[];
  checkpoints: CheckpointProgress[];
  created_at: string;
  updated_at: string;
};

export type LabFile = { path: string; content: string; editable: boolean };

export type Diagnostic = {
  severity: "error" | "warning" | "info";
  category: "syntax" | "elaboration" | "simulation" | "infrastructure" | "unknown";
  message: string;
  file?: string | null;
  line?: number | null;
  column?: number | null;
};

export type TestCase = { name: string; status: "pass" | "fail" | "error"; message: string };
export type TestSummary = { passed: number; failed: number; errors: number; cases: TestCase[] };

export type LabResult = {
  stage: "compile" | "elaboration" | "simulation" | "infrastructure";
  compile: { ok: boolean; diagnostics: Diagnostic[] };
  tests: TestSummary;
  hidden?: TestSummary | null;
  timed_out: boolean;
  runtime_ms: number;
  passed: boolean;
  diagnostics: Diagnostic[];
  traces: { values: Record<string, string> }[];
  artifacts: { name: string; kind: string; url?: string | null }[];
  output: string;
};

export type LabRun = {
  id: string;
  checkpoint_id: string;
  mode: "compile" | "test" | "submit";
  status: "queued" | "running" | "done" | "error";
  source_hash: string;
  result: LabResult | null;
};

export type LabMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  hint_level: number;
  run_id?: string | null;
  created_at: string;
};

export type TutorReply = {
  summary: string;
  error_category: string;
  evidence: string[];
  concept: string;
  next_step: string;
  question: string;
  hint_level: number;
};

export type AvailableGuideModel = { id: string; name: string };

export type OpenRouterConnectionResult = {
  ok: boolean;
  requested_model: string;
  served_model: string;
  fallback_used: boolean;
  key_source: "entered" | "server";
  engine?: string;
};
