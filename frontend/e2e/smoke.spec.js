import { expect, test } from "@playwright/test";

// Mock the backend so the app renders deterministically with no server running.
async function mockApi(page) {
  await page.route("**/api/health", (route) =>
    route.fulfill({
      json: {
        ok: true,
        model: "gpt-4o",
        web_search: true,
        diagrams: true,
        openai_configured: true,
      },
    }),
  );
  await page.route("**/api/question-types", (route) =>
    route.fulfill({
      json: [
        { key: "mcq", label: "Multiple Choice" },
        { key: "true_false", label: "True / False" },
      ],
    }),
  );
  // Chapters and assessments lists are empty for the smoke run.
  await page.route(/\/api\/chapters(\?.*)?$/, (route) => route.fulfill({ json: [] }));
  await page.route(/\/api\/assessments.*/, (route) => route.fulfill({ json: [] }));
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("loads the shell with header and both mode chips", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "StudyForge" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Study" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Evaluate" })).toBeVisible();
  await expect(page.getByText(/upload a new PDF to get started/i)).toBeVisible();
});

test("active Study button stays visible with a solid background in dark mode", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /toggle color mode/i }).click();

  const study = page.getByRole("button", { name: "Study" });
  await expect(study).toBeVisible();

  // Regression guard: an incomplete brand color scale made colorScheme="brand"
  // solid buttons render with a transparent background (invisible) in dark mode.
  const bg = await study.evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(bg).not.toBe("rgba(0, 0, 0, 0)");
  expect(bg).not.toBe("transparent");
});

test("switches to Evaluate mode and back", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Evaluate" }).click();
  // The Study empty-state is gone in Evaluate mode.
  await expect(page.getByText(/upload a new PDF to get started/i)).toHaveCount(0);

  await page.getByRole("button", { name: "Study" }).click();
  await expect(page.getByText(/upload a new PDF to get started/i)).toBeVisible();
});
