// Mirrors the Pydantic response schemas in backend/app/schemas/ - kept in
// sync by hand since the two projects don't share a codegen step.

export interface UserPublic {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: "subscriber" | "admin";
  charity_id: string | null;
  charity_percentage: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}

export interface CharityEvent {
  id: string;
  title: string;
  description: string | null;
  event_date: string;
  location: string | null;
}

export interface Charity {
  id: string;
  name: string;
  description: string;
  website_url: string | null;
  image_url: string | null;
  is_featured: boolean;
  created_at: string;
  events: CharityEvent[];
}

export interface Score {
  id: string;
  course: string | null;
  score: number;
  date_played: string;
  created_at: string;
}

export interface Subscription {
  plan: "monthly" | "yearly" | null;
  status: "inactive" | "active" | "cancelled" | "lapsed";
  amount: number;
  start_date: string | null;
  renewal_date: string | null;
}

export interface Winner {
  id: string;
  draw_id: string;
  user_id: string;
  match_tier: number;
  prize_amount: number;
  proof_image_url: string | null;
  verification_status: "pending" | "approved" | "rejected";
  payment_status: "pending" | "paid";
  created_at: string;
}

export interface UserDashboard {
  subscription: Subscription;
  charity: Charity | null;
  charity_percentage: number;
  scores: Score[];
  participation: { draws_entered: number; upcoming_draw: string | null };
  winnings: { total_won: number; total_paid: number; total_pending: number; winners: Winner[] };
}

export interface Draw {
  id: string;
  month: number;
  year: number;
  draw_type: "random" | "algorithmic";
  status: "draft" | "simulated" | "published";
  winning_numbers: number[] | null;
  pool_5_match: number;
  pool_4_match: number;
  pool_3_match: number;
  jackpot_rollover_in: number;
  created_at: string;
  published_at: string | null;
}

export interface DrawSimulationResult {
  draw_id: string;
  draw_type: string;
  winning_numbers: number[];
  total_participants: number;
  tiers: { match_tier: number; winner_count: number; prize_per_winner: number; pool_amount: number }[];
  jackpot_rolled_over: boolean;
}

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: "subscriber" | "admin";
  is_active: boolean;
  charity_percentage: number;
}

export interface ReportsSummary {
  total_users: number;
  active_subscribers: number;
  total_prize_pool_paid: number;
  total_prize_pool_pending: number;
  charity_contribution_total: number;
  total_draws_published: number;
  total_winners: number;
}
