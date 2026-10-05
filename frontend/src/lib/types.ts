export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_child_account: boolean;
  is_moderator: boolean;
  is_private: boolean;              
  date_of_birth: string | null;
  account_tier: string | null;
  created_at: string;
}
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Interest {
  id: string;
  slug: string;
  name: string;
  emoji: string | null;
  description: string | null;
  is_active: boolean;
}

export interface FocusMode {
  id: string;
  user_id: string;
  name: string;
  emoji: string | null;
  description: string | null;
  interest_slugs: string[];
  is_default: boolean;
  is_child_safe: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  author_id: string;
  text: string;
  interest_slug: string;
  media_urls: string[];
  ai_generated: boolean;
  ai_label_shown: boolean;
  moderation_status: string;
  moderation_reason: string | null;
  is_hidden: boolean;
  created_at: string;
  updated_at: string;
}

export interface FeedResponse {
  posts: Post[];
  count: number;
  applied_interest_slugs: string[];
  focus_mode_applied: boolean;
  focus_mode_name: string | null;
}

export interface StitchProject {
  id: string;
  moderator_id: string;
  title: string;
  description: string | null;
  interest_slug: string;
  status: string;
  allow_contributions: boolean;
  stitched_video_url: string | null;
  stitch_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface Contribution {
  id: string;
  project_id: string;
  contributor_id: string;
  video_url: string;
  caption: string | null;
  duration_seconds: number | null;
  consent_given: boolean;
  status: string;
  rejection_reason: string | null;
  order_index: number | null;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  author_id: string;
  text: string;
  interest_slug: string;
  media_urls: string[];
  community_id: string | null;
  audience: string;                  
  ai_generated: boolean;
  ai_label_shown: boolean;
  moderation_status: string;
  moderation_reason: string | null;
  is_hidden: boolean;
  created_at: string;
  updated_at: string;
  reaction_count: number;
  is_liked_by_me: boolean;
}
export interface PublicProfile {
  id: string;
  username: string;
  display_name: string | null;
  is_moderator: boolean;
  is_child_account: boolean;
  is_private: boolean;              
  date_of_birth: string | null;
  account_tier: string | null;
  created_at: string;
  post_count: number;
  likes_received: number;
  follower_count: number;           
  following_count: number;          
  is_following: boolean;            
}

export interface UserProfileResponse {
  profile: PublicProfile;
  posts: Post[];
}

export interface Community {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  emoji: string | null;
  interest_slug: string;
  creator_id: string;
  is_public: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
  is_member: boolean;
  is_moderator: boolean;
}

export interface CommunityListResponse {
  communities: Community[];
  count: number;
}

export interface JoinLeaveResponse {
  community_id: string;
  is_member: boolean;
  member_count: number;
  message: string;
}

export interface FollowResponse {
  user_id: string;
  username: string;
  is_following: boolean;
  follower_count: number;
}

export interface BlockResponse {
  user_id: string;
  username: string;
  is_blocked: boolean;
}

export interface BlockedUser {
  user_id: string;
  username: string;
  display_name: string | null;
}

export interface PublicUserBrief {
  id: string;
  username: string;
  display_name: string | null;
  is_private: boolean;
}