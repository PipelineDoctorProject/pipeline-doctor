import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import useAuthStore from "../store/authStore";

export default function VerifyOtpPage() {

  const navigate = useNavigate();
  const location = useLocation();

  const email = location.state?.email;

  const verifyOtp = useAuthStore(
    (state) => state.verifyOtp
  );

  const [otp, setOtp] = useState("");

  const handleVerify = async (e) => {
    e.preventDefault();

    try {

      const response = await verifyOtp(email, otp);

      if (response.onboarding_required) {
        navigate("/onboarding");
      } else {
        navigate("/dashboard");
      }

    } catch (err) {
      alert(err.detail || "OTP verification failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">

      <form
        onSubmit={handleVerify}
        className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md"
      >

        <h1 className="text-3xl font-bold mb-6 text-center">
          Verify OTP
        </h1>

        <input
          type="text"
          placeholder="Enter OTP"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          className="w-full border p-3 rounded-lg mb-4"
        />

        <button
          type="submit"
          className="w-full bg-black text-white p-3 rounded-lg"
        >
          Verify OTP
        </button>
      </form>
    </div>
  );
}