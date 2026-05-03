"use client";

import React, { Component, ReactNode, ErrorInfo } from "react";

interface Props {
  children: ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary for graceful error handling.
 * Catches render errors in child components and shows a recovery UI.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[VoteGuide] Error Boundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
            padding: 32,
            background: "var(--bg-primary)",
            color: "var(--text-primary)",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 48,
              marginBottom: 16,
            }}
            aria-hidden="true"
          >
            ⚠️
          </div>
          <h2
            style={{
              fontSize: 20,
              fontWeight: 700,
              marginBottom: 8,
            }}
          >
            Something went wrong
          </h2>
          <p
            style={{
              fontSize: 14,
              color: "var(--text-secondary)",
              marginBottom: 24,
              maxWidth: 400,
              lineHeight: 1.5,
            }}
          >
            {this.props.fallbackMessage ||
              "VoteGuide encountered an unexpected error. Please refresh the page to continue."}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: "12px 28px",
              borderRadius: 12,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              color: "white",
              border: "none",
              fontWeight: 600,
              fontSize: 14,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Refresh Page
          </button>
          {this.state.error && (
            <details
              style={{
                marginTop: 20,
                fontSize: 12,
                color: "var(--text-muted)",
                maxWidth: 500,
                textAlign: "left",
              }}
            >
              <summary style={{ cursor: "pointer" }}>Error details</summary>
              <pre
                style={{
                  marginTop: 8,
                  padding: 12,
                  borderRadius: 8,
                  background: "var(--bg-glass)",
                  overflow: "auto",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                }}
              >
                {this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
