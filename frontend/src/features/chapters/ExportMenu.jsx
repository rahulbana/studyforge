import {
  Button,
  Menu,
  MenuButton,
  MenuDivider,
  MenuGroup,
  MenuItem,
  MenuList,
} from "@chakra-ui/react";
import { FiDownload } from "react-icons/fi";
import { exportUrl } from "../../api/chapters";
import { downloadFile } from "../../lib/download";

export default function ExportMenu({ chapter, questionCount }) {
  const download = (fmt, include, layout = "full") =>
    downloadFile(exportUrl(chapter.id, fmt, include, layout));
  const disabled = chapter.notes_status !== "ready" && questionCount === 0;
  const noQuestions = questionCount === 0;

  return (
    <Menu>
      <MenuButton as={Button} leftIcon={<FiDownload />} variant="outline" isDisabled={disabled}>
        Export
      </MenuButton>
      <MenuList>
        <MenuGroup title="PDF">
          <MenuItem onClick={() => download("pdf", ["notes", "questions"])}>
            Notes + Questions
          </MenuItem>
          <MenuItem onClick={() => download("pdf", ["notes"])}>Notes only</MenuItem>
          <MenuItem onClick={() => download("pdf", ["questions"])}>Questions only</MenuItem>
        </MenuGroup>
        <MenuDivider />
        <MenuGroup title="Word (DOCX)">
          <MenuItem onClick={() => download("docx", ["notes", "questions"])}>
            Notes + Questions
          </MenuItem>
          <MenuItem onClick={() => download("docx", ["notes"])}>Notes only</MenuItem>
          <MenuItem onClick={() => download("docx", ["questions"])}>Questions only</MenuItem>
        </MenuGroup>
        <MenuDivider />
        <MenuGroup title="Worksheet (no answers + key)">
          <MenuItem isDisabled={noQuestions} onClick={() => download("pdf", ["questions"], "worksheet")}>
            Worksheet — PDF
          </MenuItem>
          <MenuItem isDisabled={noQuestions} onClick={() => download("docx", ["questions"], "worksheet")}>
            Worksheet — Word
          </MenuItem>
        </MenuGroup>
      </MenuList>
    </Menu>
  );
}
