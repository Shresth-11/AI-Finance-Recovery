"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Search,
  Filter,
  Download,
  X,
  ArrowUp,
  ArrowDown,
  Eye,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { formatINR, formatDate } from "@/lib/utils";
import { fetchApi, getExportCsvUrl } from "@/lib/api";
import { ExceptionDrawer } from "@/components/exceptions/exception-drawer";

function ExceptionsExplorerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Filter States initialized from URL params or defaults
  const [search, setSearch] = React.useState(searchParams.get("search") || "");
  const [debouncedSearch, setDebouncedSearch] = React.useState(search);
  const [severity, setSeverity] = React.useState(searchParams.get("severity") || "");
  const [status, setStatus] = React.useState(searchParams.get("status") || "");
  const [exceptionType, setExceptionType] = React.useState(searchParams.get("type") || "");
  const [minAmount, setMinAmount] = React.useState(searchParams.get("min_amount") || "");
  const [maxAmount, setMaxAmount] = React.useState(searchParams.get("max_amount") || "");
  const [sortBy, setSortBy] = React.useState(searchParams.get("sort_by") || "priority");
  const [sortOrder, setSortOrder] = React.useState(searchParams.get("sort_order") || "desc");
  const [page, setPage] = React.useState(parseInt(searchParams.get("page") || "1", 10));
  const [pageSize] = React.useState(20);
  const [onlyOpen, setOnlyOpen] = React.useState(searchParams.get("only_open") === "true");

  // API State
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Selected Exception Drawer modal state
  const [drawerId, setDrawerId] = React.useState<string | number | null>(null);

  // Debounce search input (300ms)
  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  // Sync state to URL Query Parameters
  React.useEffect(() => {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (severity) params.set("severity", severity);
    if (status) params.set("status", status);
    if (exceptionType) params.set("type", exceptionType);
    if (minAmount) params.set("min_amount", minAmount);
    if (maxAmount) params.set("max_amount", maxAmount);
    if (sortBy) params.set("sort_by", sortBy);
    if (sortOrder) params.set("sort_order", sortOrder);
    if (page > 1) params.set("page", String(page));
    if (onlyOpen) params.set("only_open", "true");

    const queryStr = params.toString();
    router.replace(`/exceptions${queryStr ? `?${queryStr}` : ""}`, { scroll: false });
  }, [debouncedSearch, severity, status, exceptionType, minAmount, maxAmount, sortBy, sortOrder, page, onlyOpen, router]);

  // Fetch exceptions from FastAPI backend
  const loadExceptions = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const activeStatus = onlyOpen ? "OPEN" : status;
      const endpoint = `/exceptions?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&sort_order=${sortOrder}${
        debouncedSearch ? `&search=${encodeURIComponent(debouncedSearch)}` : ""
      }${severity ? `&severity=${severity}` : ""}${activeStatus ? `&status=${activeStatus}` : ""}${
        exceptionType ? `&exception_type=${exceptionType}` : ""
      }${minAmount ? `&min_amount=${minAmount}` : ""}${maxAmount ? `&max_amount=${maxAmount}` : ""}`;

      const res = await fetchApi<any>(endpoint);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load exceptions data from backend.");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, sortBy, sortOrder, debouncedSearch, severity, status, onlyOpen, exceptionType, minAmount, maxAmount]);

  React.useEffect(() => {
    loadExceptions();
  }, [loadExceptions]);

  const handleExportFilteredCsv = () => {
    const csvUrl = getExportCsvUrl({
      search: debouncedSearch,
      severity,
      status: onlyOpen ? "OPEN" : status,
      exception_type: exceptionType,
      min_amount: minAmount,
      max_amount: maxAmount,
    });
    window.open(csvUrl, "_blank");
    toast.info("Downloading filtered exceptions CSV...");
  };

  const handleResetFilters = () => {
    setSearch("");
    setDebouncedSearch("");
    setSeverity("");
    setStatus("");
    setExceptionType("");
    setMinAmount("");
    setMaxAmount("");
    setSortBy("priority");
    setSortOrder("desc");
    setPage(1);
    setOnlyOpen(false);
  };

  // Calculate filtered discrepancy total
  const filteredDiscrepancySum = React.useMemo(() => {
    if (!data?.items) return 0;
    return data.items.reduce((sum: number, item: any) => sum + (item.discrepancy_amount || 0), 0);
  }, [data]);

  return (
    <div className="space-y-4">
      {/* Sticky Header Bar */}
      <div className="sticky top-14 z-20 bg-background/95 backdrop-blur border-b py-3 -mx-6 px-6 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Exceptions Explorer & Triage
            </h1>
            <Badge variant="outline" className="font-mono text-[11px] font-semibold bg-muted">
              {data ? `${data.total_count} Exceptions` : "Loading..."}
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
            <span>
              Filtered Discrepancy:{" "}
              <strong className="font-mono text-amber-700 dark:text-amber-400 font-semibold">
                {formatINR(filteredDiscrepancySum)}
              </strong>
            </span>
            <span>•</span>
            <span>Sorted by: <strong className="font-semibold text-foreground uppercase">{sortBy} ({sortOrder})</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportFilteredCsv}
            className="gap-1.5 text-xs shadow-sm"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export Filtered CSV</span>
          </Button>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="space-y-3 bg-card p-3.5 rounded-lg border shadow-2xs">
        <div className="flex flex-col lg:flex-row items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search exception code, order ID, payment ID, UTR, invoice ID..."
              className="pl-8 text-xs h-9"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Quick Dropdown Selects */}
          <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
            {/* Severity Filter */}
            <select
              value={severity}
              onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-input bg-background px-2.5 text-xs font-medium outline-none"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>

            {/* Status Filter */}
            <select
              value={status}
              disabled={onlyOpen}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-input bg-background px-2.5 text-xs font-medium outline-none disabled:opacity-50"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="INVESTIGATING">INVESTIGATING</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="IGNORED">IGNORED</option>
              <option value="ESCALATED">ESCALATED</option>
            </select>

            {/* Exception Type Filter */}
            <select
              value={exceptionType}
              onChange={(e) => { setExceptionType(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-input bg-background px-2.5 text-xs font-medium outline-none max-w-[160px] truncate"
            >
              <option value="">All Categories</option>
              <option value="DUPLICATE_PAYMENT">Duplicate Payment</option>
              <option value="MISSING_SETTLEMENT">Missing Settlement</option>
              <option value="PAYMENT_WITHOUT_ORDER">Payment Without Order</option>
              <option value="SETTLEMENT_MISMATCH">Settlement Mismatch</option>
              <option value="DELAYED_SETTLEMENT">Delayed Settlement</option>
              <option value="DUPLICATE_SETTLEMENT">Duplicate Settlement</option>
              <option value="PARTIAL_PAYMENT">Partial Payment</option>
              <option value="OVERPAYMENT">Overpayment</option>
              <option value="REFUND_MISMATCH">Refund Mismatch</option>
              <option value="INVOICE_MISMATCH">Invoice Mismatch</option>
              <option value="FEE_ANOMALY">Fee Anomaly</option>
              <option value="FUZZY_MATCH">Fuzzy Match</option>
            </select>

            {/* Sort Field Select */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-2.5 text-xs font-medium outline-none"
            >
              <option value="priority">Sort: Priority</option>
              <option value="amount">Sort: Discrepancy Amount</option>
              <option value="severity">Sort: Severity</option>
              <option value="confidence">Sort: AI Confidence</option>
              <option value="created_at">Sort: Date</option>
            </select>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              className="h-9 w-9 border"
              title={`Sort Direction: ${sortOrder}`}
            >
              {sortOrder === "desc" ? <ArrowDown className="h-3.5 w-3.5" /> : <ArrowUp className="h-3.5 w-3.5" />}
            </Button>
          </div>
        </div>

        {/* Toggle & Active Filter Chips Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-2.5 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-1.5 font-medium text-foreground cursor-pointer select-none">
              <input
                type="checkbox"
                checked={onlyOpen}
                onChange={(e) => { setOnlyOpen(e.target.checked); setPage(1); }}
                className="h-3.5 w-3.5 rounded border-input"
              />
              <span>Only Needs Review (OPEN)</span>
            </label>

            {/* Active Chips */}
            {(debouncedSearch || severity || status || exceptionType || minAmount || maxAmount || onlyOpen) && (
              <div className="flex flex-wrap items-center gap-1.5 border-l pl-2.5 ml-1">
                {debouncedSearch && (
                  <Badge variant="secondary" className="gap-1 text-[10px] py-0 h-5">
                    Search: {debouncedSearch}
                    <X className="h-3 w-3 cursor-pointer" onClick={() => setSearch("")} />
                  </Badge>
                )}
                {severity && (
                  <Badge variant="secondary" className="gap-1 text-[10px] py-0 h-5">
                    Severity: {severity}
                    <X className="h-3 w-3 cursor-pointer" onClick={() => setSeverity("")} />
                  </Badge>
                )}
                {status && !onlyOpen && (
                  <Badge variant="secondary" className="gap-1 text-[10px] py-0 h-5">
                    Status: {status}
                    <X className="h-3 w-3 cursor-pointer" onClick={() => setStatus("")} />
                  </Badge>
                )}
                {exceptionType && (
                  <Badge variant="secondary" className="gap-1 text-[10px] py-0 h-5">
                    Type: {exceptionType}
                    <X className="h-3 w-3 cursor-pointer" onClick={() => setExceptionType("")} />
                  </Badge>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleResetFilters}
                  className="h-5 px-1.5 text-[10px] text-muted-foreground hover:text-foreground"
                >
                  Clear All
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error State Banner */}
      {error && (
        <ErrorState
          title="Failed to load exceptions"
          message={error}
          onRetry={loadExceptions}
        />
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="space-y-2">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-md" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && data?.items?.length === 0 && (
        <EmptyState
          title="No exceptions match active filters"
          description="No exceptions match these filters. Try clearing a filter or changing the search term."
          actionLabel="Clear All Filters"
          onAction={handleResetFilters}
          icon={AlertTriangle}
        />
      )}

      {/* Dense High-Performance Data Table */}
      {!loading && data && data.items.length > 0 && (
        <Card className="overflow-hidden border">
          <CardContent className="p-0">
            <Table>
              <TableHeader className="sticky top-0 bg-muted/60 z-10 backdrop-blur">
                <TableRow>
                  <TableHead>Priority</TableHead>
                  <TableHead>Exception Code</TableHead>
                  <TableHead>Category / Type</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Related Entities</TableHead>
                  <TableHead className="text-right">Money at Risk</TableHead>
                  <TableHead>AI Conf.</TableHead>
                  <TableHead>Detected</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((row: any) => {
                  const sevLabel = row.severity.toUpperCase();
                  const isCritical = sevLabel === "CRITICAL";

                  return (
                    <TableRow
                      key={row.id}
                      onClick={() => setDrawerId(row.id)}
                      className={`cursor-pointer transition-colors hover:bg-muted/60 ${
                        isCritical ? "bg-red-50/20 dark:bg-red-950/10" : ""
                      }`}
                    >
                      {/* Priority Score */}
                      <TableCell className="font-bold tabular-nums text-primary font-mono">
                        {row.priority_score ? row.priority_score.toFixed(1) : "80.0"}
                      </TableCell>

                      {/* Exception Code */}
                      <TableCell className="font-mono font-semibold text-foreground">
                        <Link href={`/exceptions/${row.id}`} onClick={(e) => e.stopPropagation()} className="hover:underline text-primary">
                          {row.exception_code}
                        </Link>
                      </TableCell>

                      {/* Type */}
                      <TableCell className="font-medium text-foreground">
                        {row.exception_type.replace(/_/g, " ")}
                      </TableCell>

                      {/* Severity Badge + Text Label */}
                      <TableCell>
                        <Badge variant={row.severity.toLowerCase() as any} className="uppercase text-[10px] font-bold">
                          ● {sevLabel}
                        </Badge>
                      </TableCell>

                      {/* Status Badge */}
                      <TableCell>
                        <Badge
                          variant={row.status === "RESOLVED" ? "resolved" : "outline"}
                          className="text-[10px]"
                        >
                          {row.status}
                        </Badge>
                      </TableCell>

                      {/* Related Entity IDs */}
                      <TableCell className="font-mono text-[11px] text-muted-foreground">
                        {row.order_id && <div>Ord: {row.order_id}</div>}
                        {row.payment_id && <div>Pay: {row.payment_id}</div>}
                        {row.settlement_id && <div>Set: {row.settlement_id}</div>}
                        {row.invoice_id && <div>Inv: {row.invoice_id}</div>}
                      </TableCell>

                      {/* Discrepancy Amount */}
                      <TableCell className="text-right font-bold tabular-nums text-foreground">
                        {formatINR(row.discrepancy_amount)}
                      </TableCell>

                      {/* AI Confidence */}
                      <TableCell className="font-mono text-muted-foreground">
                        {row.ai_confidence_score ? `${(row.ai_confidence_score * 100).toFixed(0)}%` : "95%"}
                      </TableCell>

                      {/* Detected Date */}
                      <TableCell className="text-muted-foreground text-[11px]">
                        {formatDate(row.created_at)}
                      </TableCell>

                      {/* Action Button */}
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDrawerId(row.id);
                          }}
                          className="h-7 px-2 text-xs gap-1 hover:bg-primary hover:text-primary-foreground"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>Review</span>
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>

          {/* Pagination Footer */}
          <div className="flex items-center justify-between px-4 py-3 border-t text-xs text-muted-foreground bg-muted/20">
            <div>
              Showing <strong className="font-semibold text-foreground">{(page - 1) * pageSize + 1}</strong> to{" "}
              <strong className="font-semibold text-foreground">
                {Math.min(page * pageSize, data.total_count)}
              </strong>{" "}
              of <strong className="font-semibold text-foreground">{data.total_count}</strong> items
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="h-8 gap-1 text-xs"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </Button>
              <span className="font-mono px-2">
                Page {data.page} of {data.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className="h-8 gap-1 text-xs"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Exception Review Drawer */}
      <ExceptionDrawer
        exceptionId={drawerId}
        onClose={() => setDrawerId(null)}
        onStatusUpdated={loadExceptions}
      />
    </div>
  );
}

export default function ExceptionsExplorerPage() {
  return (
    <React.Suspense fallback={<Skeleton className="h-96 w-full rounded-lg" />}>
      <ExceptionsExplorerContent />
    </React.Suspense>
  );
}
