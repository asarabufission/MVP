import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useSetAssignmentIdentifier } from "@/hooks/useClients";
import { useUiStore } from "@/stores/ui-store";
import type { ApiError, ClientAssignment } from "@/types/api";

const schema = z
  .object({
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
      message: "Provide both fields, or leave both blank to clear.",
      path: ["identifierType"],
    },
  );

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  clientId: string;
  clientDefault: { type: string; value: string };
  assignment: ClientAssignment | null;
}

export function SetIdentifierModal({
  open,
  onClose,
  clientId,
  clientDefault,
  assignment,
}: Props) {
  const set = useSetAssignmentIdentifier();
  const pushToast = useUiStore((s) => s.pushToast);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { identifierType: "", identifierValue: "" },
  });

  useEffect(() => {
    if (!open) return;
    setServerError(null);
    reset({
      identifierType: assignment?.identifierType ?? "",
      identifierValue: assignment?.identifierValue ?? "",
    });
  }, [open, assignment, reset]);

  if (!open || !assignment) return null;

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await set.mutateAsync({
        clientId,
        datasourceId: assignment.datasourceId,
        identifierType: values.identifierType ?? "",
        identifierValue: values.identifierValue ?? "",
      });
      pushToast({ type: "success", message: "Identifier saved" });
      onClose();
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const code = axiosError.response?.data?.code;
      if (code === "INVALID_IDENTIFIER") {
        setServerError("Both fields must be filled, or both blank to clear.");
      } else if (code === "ASSIGNMENT_INACTIVE") {
        setServerError("This assignment is inactive and cannot be edited.");
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 font-sans text-text shadow-xl">
        <h2 className="text-lg font-semibold">
          Set Identifier — {assignment.datasourceName}
        </h2>
        <p className="mt-1 text-xs text-muted">
          Override the client default{" "}
          <span className="font-mono text-text">
            {clientDefault.type} = {clientDefault.value}
          </span>{" "}
          for this datasource. Leave both fields blank to clear the override.
        </p>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-5 space-y-4"
          noValidate
        >
          <Input
            label="Identifier Type"
            autoFocus
            {...register("identifierType")}
            error={errors.identifierType?.message}
            placeholder="e.g. COMPANY_NAME_EQUALS"
          />
          <Input
            label="Identifier Value"
            {...register("identifierValue")}
            error={errors.identifierValue?.message}
            placeholder="e.g. Acme Corp Inc."
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
              Save
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
