import { AuthContext } from "../auth/AuthContext";
import Layout from "../components/Layout";

const fakeUser = { username: "cl01", role: "cliente", role_name: "Cliente" };

export default function PreviewLayout() {
  return (
    <AuthContext.Provider value={{ user: fakeUser, loading: false, logout: async () => {} }}>
      <Layout />
    </AuthContext.Provider>
  );
}