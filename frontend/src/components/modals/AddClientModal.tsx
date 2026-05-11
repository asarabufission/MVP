import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCreateClient, useUpdateClient } from "@/hooks/useClients";
import { useUiStore } from "@/stores/ui-store";
import type { ApiError, ClientDetail } from "@/types/api";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(160),
  description: z.string().max(2000).optional(),
  defaultIdentifierType: z.string().min(1, "Required").max(60),
  defaultIdentifierValue: z.string().min(1, "Required").max(160),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  initial?: ClientDetail | null;
}

export function AddClientModal({ open, onClose, initial }: Props) {
  const isEdit = Boolean(initial);
  const create = useCreateClient();
  const update = useUpdateClient(initial?.id);
  const pushToast = useUiStore((s) => s.pushToast);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      description: "",
      defaultIdentifierType: "",
      defaultIdentifierValue: "",
    },
  });

  useEffect(() => {
    if (!open) return;
    setServerError(null);
    reset({
      name: initial?.name ?? "",
      description: initial?.description ?? "",
      defaultIdentifierType: initial?.defaultIdentifierType ?? "",
      defaultIdentifierValue: initial?.defaultIdentifierValue ?? "",
    });
  }, [open, initial, reset]);

  if (!open) return null;

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    const body = {
      name: values.name,
      description: values.description ? values.description : null,
      defaultIdentifierType: values.defaultIdentifierType,
      defaultIdentifierValue: values.defaultIdentifierValue,
    };
    try {
      if (isEdit) {
        await update.mutateAsync(body);
        pushToast({ type: "success", message: "Client updated" });
      } else {
        await create.mutateAsync(body);
        pushToast({ type: "success", message: "Client created" });
      }
      onClose();
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const code = axiosError.response?.data?.code;
      if (code === "CLIENT_NAME_TAKEN") {
        setError("name", { message: "Client name already exists" });
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 font-sans text-text shadow-xl">
        <h2 className="text-lg font-semibold">
          {isEdit ? "Edit Client" : "Add Client"}
        </h2>
        <p className="mt-1 text-xs text-muted">
          The default identifier is used as a fallback for assignments that
          don't override it.
        </p>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-5 space-y-4"
          noValidate
        >
          <Input
            label="Name"
            autoFocus
            {...register("name")}
            error={errors.name?.message}
          />
          <div className="space-y-1">
            <label
              htmlFor="description"
              className="block text-xs font-medium uppercase tracking-wide text-muted"
            >
              Description
            </label>
            <textarea
              id="description"
              rows={3}
              {...register("description")}
              className="w-full rounded-md border border-border bg-surface2 px-3 py-2 text-sm text-text placeholder-dim focus:border-accent focus:outline-none"
              placeholder="Optional"
            />
            {errors.description && (
              <p className="text-xs text-red">{errors.description.message}</p>
            )}
          </div>
          <Input
            label="Default Identifier Type"
            {...register("defaultIdentifierType")}
            error={errors.defaultIdentifierType?.message}
            placeholder="e.g. EMAIL_DOMAIN_CONTAINS"
          />
          <Input
            label="Default Identifier Value"
            {...register("defaultIdentifierValue")}
            error={errors.defaultIdentifierValue?.message}
            placeholder="e.g. acme.com"
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
              {isEdit ? "Save" : "Create"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
