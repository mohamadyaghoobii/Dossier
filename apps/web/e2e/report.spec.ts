import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /stakeholder-ready reports/i })).toBeVisible();
});

test("generates an executive report from a sample", async ({ page }) => {
  await page.getByRole("button", { name: /^Mixed Results/ }).click();
  await page.getByRole("button", { name: "Executive", exact: true }).click();
  await page.getByRole("button", { name: /Generate report/ }).click();

  await expect(page.getByText("Report Score")).toBeVisible();
  await expect(page.getByText(/Grade [A-F]/)).toBeVisible();

  await page.getByRole("button", { name: "Markdown", exact: true }).click();
  await expect(page.locator("pre.raw")).toContainText("Executive");

  await page.getByRole("button", { name: "HTML preview" }).click();
  await expect(page.locator("iframe.html-frame")).toBeVisible();
});

test("generates a technical report with findings", async ({ page }) => {
  await page.getByRole("button", { name: /^Technical Input/ }).click();
  await page.getByRole("button", { name: "Technical", exact: true }).click();
  await page.getByRole("button", { name: /Generate report/ }).click();

  await expect(page.getByText("Severity breakdown")).toBeVisible();
  await expect(page.getByText("Top risks")).toBeVisible();
});

test("generates a remediation plan", async ({ page }) => {
  await page.getByRole("button", { name: /^Remediation Input/ }).click();
  await page.getByRole("button", { name: "Remediation", exact: true }).click();
  await page.getByRole("button", { name: /Generate report/ }).click();

  await expect(page.getByText("Remediation Plan").first()).toBeVisible();
});

test("shows a clean empty state for empty findings", async ({ page }) => {
  await page.getByRole("button", { name: /^Empty Findings/ }).click();
  await page.getByRole("button", { name: /Generate report/ }).click();

  await expect(page.getByText("Report Score")).toBeVisible();
  await expect(page.getByText("100")).toBeVisible();
});
