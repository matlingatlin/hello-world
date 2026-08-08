import { useAuth } from "@clerk/clerk-react";
import { useMemo } from "react";
import { createApi } from "./api";

/** API client bound to the current Clerk session. */
export function useApi() {
  const { getToken } = useAuth();
  return useMemo(() => createApi(() => getToken()), [getToken]);
}
