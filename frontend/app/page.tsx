"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";

export default function Home() {
  const [balance, setBalance] = useState<any>(null);
  const [payouts, setPayouts] = useState<any[]>([]);
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const fetchData = async () => {
    const balanceRes = await axios.get("http://127.0.0.1:8000/api/v1/balance");
    const payoutRes = await axios.get("http://127.0.0.1:8000/api/v1/payouts/list");

    setBalance(balanceRes.data);
    setPayouts(payoutRes.data);
  };

  useEffect(() => {
    fetchData();

    const interval = setInterval(() => {
      fetchData();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const createPayout = async () => {
    if (!amount || Number(amount) <= 0) {
      toast.error("Enter valid payout amount");
      return;
    }

    try {
      setLoading(true);

      await axios.post(
        "http://127.0.0.1:8000/api/v1/payouts",
        {
          amount_paise: Number(amount) * 100,
          bank_account_id: 3,
        },
        {
          headers: {
            "Idempotency-Key": crypto.randomUUID(),
          },
        }
      );

      toast.success("Payout created successfully");
setAmount("");
fetchData();
    } catch (err: any) {
      toast.error(err?.response?.data?.error || "Payout failed");
    } finally {
      setLoading(false);
    }
  };

  const filteredPayouts = payouts.filter((payout) => {
  const matchesSearch = payout.id.toString().includes(search);

  const matchesStatus =
    statusFilter === "ALL" || payout.status === statusFilter;

  return matchesSearch && matchesStatus;
});

const retryPayout = async (payoutId: number) => {
  try {
    await axios.post(
      `http://127.0.0.1:8000/api/v1/payouts/${payoutId}/retry`
    );

    toast.success("Retry initiated");
    fetchData();
  } catch (err: any) {
    toast.error(err?.response?.data?.error || "Retry failed");
  }
};

  const getStatusColor = (status: string) => {
    if (status === "COMPLETED") return "bg-green-100 text-green-700";
    if (status === "FAILED") return "bg-red-100 text-red-700";
    return "bg-yellow-100 text-yellow-700";
  };

  return (
    <main className="min-h-screen bg-slate-100 p-8">
  <Toaster position="top-right" />

  <div className="max-w-5xl mx-auto">

        <h1 className="text-4xl font-bold mb-8">Payout Dashboard</h1>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Merchant Balance</h2>

            {balance ? (
              <div className="space-y-2">
                <p className="text-lg">
                  Available: <span className="font-bold text-green-600">₹{balance.available_balance / 100}</span>
                </p>
                <p className="text-lg">
                  Held: <span className="font-bold text-yellow-600">₹{balance.held_balance / 100}</span>
                </p>
              </div>
            ) : (
              <p>Loading balance...</p>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Create Payout</h2>

            <input
              type="number"
              placeholder="Amount in ₹"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="border rounded-lg px-4 py-2 w-full mb-4"
            />

            <button
              onClick={createPayout}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg disabled:opacity-50"
            >
              {loading ? "Creating..." : "Create Payout"}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
  <h2 className="text-xl font-semibold">Recent Payouts</h2>

  <div className="flex gap-3">
    <input
      type="text"
      placeholder="Search by ID"
      value={search}
      onChange={(e) => setSearch(e.target.value)}
      className="border rounded-lg px-3 py-2"
    />

    <select
      value={statusFilter}
      onChange={(e) => setStatusFilter(e.target.value)}
      className="border rounded-lg px-3 py-2"
    >
      <option value="ALL">All</option>
      <option value="PENDING">Pending</option>
      <option value="COMPLETED">Completed</option>
      <option value="FAILED">Failed</option>
    </select>
  </div>
</div>

          <div className="space-y-4">
            {filteredPayouts.map((payout) => (
              <div
                key={payout.id}
                className="border rounded-xl p-4 flex justify-between items-center"
              >
                <div>
                  <p className="font-semibold">Payout #{payout.id}</p>
                  <p>₹{payout.amount_paise / 100}</p>
                </div>

                <div className="flex items-center gap-3">
  <span
    className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
      payout.status
    )}`}
  >
    {payout.status}
  </span>

  {payout.status === "FAILED" && (
    <button
      onClick={() => retryPayout(payout.id)}
      className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-lg text-sm"
    >
      Retry
    </button>
  )}
</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </main>
  );
}