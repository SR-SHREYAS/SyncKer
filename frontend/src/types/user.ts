export type UserIdentity = {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
};

export type User = UserIdentity & {
  created_at: string;
  updated_at: string;
};
