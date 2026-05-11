import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";

export default function OnboardingPage() {

  const navigate = useNavigate();

  const createCompany = useAuthStore(
    (state) => state.createCompany
  );

  const [companyName, setCompanyName] = useState("");

  const handleCreateCompany = async (e) => {
    e.preventDefault();

    try {

      await createCompany(companyName);

      navigate("/dashboard");

    } catch (err) {
      alert(err.detail || "Company creation failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">

      <form
        onSubmit={handleCreateCompany}
        className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md"
      >

        <h1 className="text-3xl font-bold mb-6 text-center">
          Create Company
        </h1>

        <input
          type="text"
          placeholder="Company Name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          className="w-full border p-3 rounded-lg mb-4"
        />

        <button
          type="submit"
          className="w-full bg-black text-white p-3 rounded-lg"
        >
          Create Company
        </button>
      </form>
    </div>
  );
}