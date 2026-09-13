import { useEffect, useState } from "react";
import { getHealth } from "../api/meta";

export function useHealth() {
  const [health, setHealth] = useState(null);
  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);
  return health;
}
