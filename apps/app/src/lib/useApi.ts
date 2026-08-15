import { useMemo } from "react";
import { createApi } from "./api";
import { useAuthToken } from "./auth";

/** API client bound to the current session, whichever provider issued it. */
export function useApi() {
  const getToken = useAuthToken();
  return useMemo(() => createApi(getToken), [getToken]);
}
