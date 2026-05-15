import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useAssignDatasource } from "@/hooks/useClientAssignments";
import { useDatasourceList } from "@/hooks/useDatasources";
import { useUiStore } from "@/stores/ui-store";
import type { ApiError } from "@/types/api";

const schema = z
  .object({
    datasourceId: z.string().min(1, "Select a datasource"),
    identifierType: z.string().max(60).optional().or(z.literal("")),
    identifierValue: z.string().max(160).optional().or(z.literal("")),
  })
  .refine(
    (v) => {
      const t = (v.identifierType ?? "").trim();
      const val = (v.identifierValue ?? "").trim();
      return (t === "" && val === "") || (t !== "" && val !== "");
    },
    {
      message: "Provide both fields, or leave both blank to use the client default.",
      path: ["identifierType"],
    },
  );

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  clientId: string;
  clientDefault: { type: string; value: string };
  excludeDatasourceIds: string[];
}

export function AssignDatasourceModal({
  open,
  onClose,
  clientId,
  clientDefault,
  excludeDatasourceIds,
}: Props) {
  const datasources = useDatasourceList({ status: "ACTIVE" });
  const assign = useAssignDatasource(clientId);
  const pushToast = useUiStore((s) => s.pushToast);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { datasourceId: "", identifierType: "", identifierValue: "" },
  });

  useEffect(() => {
    if (!open) return;
    setServerError(null);
    reset({ datasourceId: "", identifierType: "", identifierValue: "" });
  }, [open, reset]);

  const available = useMemo(() => {
    const excluded = new Set(excludeDatasourceIds);
    return (datasources.data?.items ?? []).filter((d) => !excluded.has(d.id));
  }, [datasources.data, excludeDatasourceIds]);

  if (!open) return null;

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await assign.mutateAsync({
        datasourceId: values.datasourceId,
        identifierType: values.identifierType?.trim() || null,
        identifierValue: values.identifierValue?.trim() || null,
      });
      pushToast({ type: "success", message: "Datasource assigned" });
      onClose();
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const code = axiosError.response?.data?.code;
      if (code === "ALREADY_ASSIGNED") {
        setServerError("This datasource is already assigned to this client.");
      } else if (code === "ASSIGNMENT_INACTIVE") {
        setServerError("This datasource is inactive and cannot be assigned.");
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 font-sans text-text shadow-xl">
        <h2 className="text-lg font-semibold">Assign Datasource</h2>
        <p className="mt-1 text-xs text-muted">
          Pick a datasource to assign to this client. Identifier defaults to{" "}
          <span className="font-mono text-text">
            {clientDefault.type} = {clientDefault.value}
          </span>{" "}
          unless overridden below.
        </p>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-5 space-y-4"
          noValidate
        >
          <Select
            label="Datasource"
            {...register("datasourceId")}
            error={errors.datasourceId?.message}
            disabled={datasources.isLoading || available.length === 0}
          >
            <option value="">
              {datasources.isLoading
                ? "Loading…"
                : available.length === 0
                  ? "No datasources available"
                  : "Select a datasource…"}
            </option>
            {available.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} — {d.category} ({d.status})
              </option>
            ))}
          </Select>
          <Input
            label="Identifier Type (optional)"
            {...register("identifierType")}
            error={errors.identifierType?.message}
            placeholder={clientDefault.type}
          />
          <Input
            label="Identifier Value (optional)"
            {...register("identifierValue")}
            placeholder={clientDefault.value}
          />
          {serverError && (
            <div
              role="alert"
              className="rounded-md border border-red/40 bg-red/10 px-3 py-2 text-xs text-red"
            >
              {serverError}
            </div>
          )}
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting}>
              Assign
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
