# E2E Test: Random Query Button

Test the "Random Query" button functionality in the Natural Language SQL Interface application.

## User Story

As a user exploring a newly uploaded dataset
I want to click a button that suggests an interesting natural language query based on my data's actual tables and columns
So that I can quickly learn what questions I can ask and run them without having to think one up myself

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the "🎲 Random Query" button is visible in the query controls area, visually separated from the Query/Upload Data button group
4. **Verify** the Random Query button is enabled

5. Open the Upload Data modal and load the "Users Data" sample data
6. Wait for the upload to succeed and the Available Tables section to show the `users` table
7. Take a screenshot after loading sample data

8. Click into the query textarea and type placeholder text: "this is placeholder text"
9. Click the "🎲 Random Query" button
10. **Verify** the query textarea no longer contains "this is placeholder text"
11. **Verify** the query textarea contains new, non-empty text
12. Take a screenshot showing the populated field after the first random query generation

13. Note the current text in the query textarea
14. Click the "🎲 Random Query" button a second time
15. **Verify** the query textarea's contents changed and are still non-empty (overwritten, not appended — the new text should not simply be the old text with more appended after it)
16. Take a screenshot showing the field after the second generation

## Success Criteria
- The "🎲 Random Query" button is visible and enabled, styled like the "Upload Data" secondary button
- Clicking the button always fully overwrites the query textarea's contents (never appends to existing text)
- The generated text is non-empty and reasonably short (consistent with a two-sentence limit)
- Clicking the button a second time overwrites the field again with new content
- 4 screenshots are taken
