import { useCallback, useEffect, useState } from "react";
import { errorsFrom } from "./friendlyErrors";

export function useLoader(load, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    load()
      .then((payload) => !cancelled && setData(payload.data))
      .catch((err) => !cancelled && setError(errorsFrom(err)[0]))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version, ...deps]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { data, loading, error, reload };
}
