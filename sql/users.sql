/****** Object:  Table [dbo].[users]    Script Date: 2022/03/07 14:09:06 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[users](
	[userid] [varchar](100) NOT NULL,
	[userpassword] [varchar](100) NOT NULL,
	[dormitory_type] [int] NOT NULL,
	[IC_IDm] [varchar](30) NOT NULL,
 CONSTRAINT [PK_users] PRIMARY KEY CLUSTERED 
(
	[userid] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

