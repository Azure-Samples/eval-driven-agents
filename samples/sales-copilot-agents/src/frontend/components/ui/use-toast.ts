import { useState } from "react"

type ToastProps = {
  title?: string
  description?: string
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastProps[]>([])

  const toast = ({ title, description }: ToastProps) => {
    setToasts([...toasts, { title, description }])
  }

  return { toast, toasts }
} 