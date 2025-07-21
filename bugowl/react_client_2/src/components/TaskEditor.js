import React, { useState } from 'react';
import './TaskEditor.css';

const TaskEditor = ({ task, isSelected, onSelect, onUpdate, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);

  const handleSave = () => {
    onUpdate({
      ...task,
      title: title.trim()
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setTitle(task.title);
    setIsEditing(false);
  };

  return (
    <div 
      className={`task-editor ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      {isEditing ? (
        <div className="task-edit-mode">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
          <div className="task-edit-buttons">
            <button onClick={(e) => { e.stopPropagation(); handleSave(); }}>Save</button>
            <button onClick={(e) => { e.stopPropagation(); handleCancel(); }}>Cancel</button>
          </div>
        </div>
      ) : (
        <div className="task-view-mode">
          <div className="task-info">
            <span className="task-title">{task.title}</span>
            <span className="task-uuid">UUID: {task.uuid}</span>
          </div>
          <div className="task-actions">
            <button onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}>Edit</button>
            <button onClick={(e) => { e.stopPropagation(); onDelete(); }}>Delete</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskEditor;
