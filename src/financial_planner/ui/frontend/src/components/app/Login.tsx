import { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Shield, ChevronLeft, LogIn, UserRound, KeyRound } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export function Login() {
  const loginUser = useAppStore((s) => s.loginUser);
  const [provider, setProvider] = useState<"google" | "microsoft" | "other" | null>(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [showProviderModal, setShowProviderModal] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !name || !provider) {
      setError("Please fill out all fields.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await loginUser(email, name, provider);
    } catch (err: any) {
      setError(err?.message || "Failed to log in.");
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSelect = (selectedProvider: "google" | "microsoft" | "other") => {
    setProvider(selectedProvider);
    setShowProviderModal(false);
    if (selectedProvider === "other") {
      setName("");
      setEmail("");
    } else {
      setName("Ney Morais");
      setEmail(`ney.morais@${selectedProvider === "google" ? "gmail.com" : "outlook.com"}`);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-background text-foreground px-4 py-12 relative overflow-hidden">
      {/* Background Decorative Shimmer */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-primary/20 to-accent/30 blur-3xl opacity-50" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-gradient-to-br from-primary/10 to-accent/20 blur-3xl opacity-50" />

      <div className="w-full max-w-[390px] relative z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="size-24 rounded-2xl overflow-hidden shadow-glow ring-2 ring-primary/40 bg-card p-1">
              <img src="/icon-dark.png?v=2" alt="Financial Planner" className="size-full object-cover rounded-xl" />
            </div>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Corporate Planning Platform
          </h1>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto font-medium">
            Volume-to-Margin Scenario Builder
          </p>
        </div>

        {/* Auth Card */}
        <Card className="border shadow-lg">
          {!provider ? (
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-xl">Welcome back</CardTitle>
                <CardDescription>Sign in to access your planning workspace</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pb-6">
                {/* Styled Login Box Trigger Button */}
                <Button
                  onClick={() => setShowProviderModal(true)}
                  className="w-full h-12 gap-2 text-sm font-semibold cursor-pointer bg-gradient-brand text-white shadow-glow hover:opacity-95"
                >
                  <KeyRound className="size-4" />
                  Sign In to Workspace
                </Button>
              </CardContent>
              <CardFooter className="flex justify-center text-xs text-muted-foreground border-t bg-muted/40 py-4">
                Authorized corporate access only. Logs are audited.
              </CardFooter>
            </>
          ) : (
            <form onSubmit={handleSubmit}>
              <CardHeader className="space-y-1 relative">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setProvider(null)}
                  className="absolute left-4 top-4 size-8"
                >
                  <ChevronLeft className="size-4" />
                </Button>
                <div className="text-center pt-2">
                  <CardTitle className="text-xl">
                    Sign in with {provider === "google" ? "Google" : provider === "microsoft" ? "Microsoft" : "Custom Credentials"}
                  </CardTitle>
                  <CardDescription>
                    Complete the secure workspace access details
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-1">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your name"
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-3">
                <Button type="submit" disabled={loading} className="w-full gap-2 cursor-pointer h-10">
                  <LogIn className="size-4" />
                  {loading ? "Authenticating..." : "Authorize Workspace Access"}
                </Button>
                <div className="text-xs text-muted-foreground text-center">
                  This simulates standard OAuth client check callback.
                </div>
              </CardFooter>
            </form>
          )}
        </Card>
      </div>

      {/* Provider Selection Modal Popup */}
      <Dialog open={showProviderModal} onOpenChange={setShowProviderModal}>
        <DialogContent className="max-w-[360px]">
          <DialogHeader className="text-center">
            <DialogTitle className="text-lg">Select Authentication Provider</DialogTitle>
            <DialogDescription>
              Choose your enterprise identity provider to continue
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-3">
            {/* Google Sign In */}
            <Button
              variant="outline"
              onClick={() => handleProviderSelect("google")}
              className="w-full h-11 justify-start gap-3 cursor-pointer text-sm font-medium hover:bg-accent/50"
            >
              <svg className="size-4 shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12.24 10.285V14.4h6.887c-.648 2.41-2.519 4.114-5.136 4.114A5.5 5.5 0 0 1 8.5 13a5.5 5.5 0 0 1 5.491-5.514c2.256 0 4.108 1.417 4.887 3.398l3.666-1.57C21.144 5.922 17.02 3.5 12.24 3.5 6.996 3.5 2.5 7.72 2.5 13c0 5.28 4.496 9.5 9.74 9.5 5.753 0 9.873-4.004 9.873-9.986a8.6 8.6 0 0 0-.17-1.729H12.24Z"
                />
              </svg>
              Continue with Google
            </Button>

            {/* Microsoft Sign In */}
            <Button
              variant="outline"
              onClick={() => handleProviderSelect("microsoft")}
              className="w-full h-11 justify-start gap-3 cursor-pointer text-sm font-medium hover:bg-accent/50"
            >
              <svg className="size-4 shrink-0" viewBox="0 0 23 23">
                <path fill="#f35325" d="M0 0h11v11H0z" />
                <path fill="#81bc06" d="M12 0h11v11H12z" />
                <path fill="#05a6f0" d="M0 12h11v11H0z" />
                <path fill="#ffba08" d="M12 12h11v11H12z" />
              </svg>
              Continue with Microsoft
            </Button>

            {/* Other Sign In */}
            <Button
              variant="outline"
              onClick={() => handleProviderSelect("other")}
              className="w-full h-11 justify-start gap-3 cursor-pointer text-sm font-medium hover:bg-accent/50"
            >
              <UserRound className="size-4 shrink-0 text-muted-foreground" />
              Continue with Other
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
