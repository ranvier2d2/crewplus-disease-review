from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Uncomment the following line to use an example of a custom tool
# from disease_review.tools.custom_tool import MyCustomTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

@CrewBase
class DiseaseReviewCrew():
	"""DiseaseReview crew"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			# tools=[MyCustomTool()], # Example of custom tool, loaded on the beginning of file
			verbose=True,
			allow_delegation=False
		)

	@agent
	def analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['analyst'],
			verbose=True,
			allow_delegation=False
		)
	
	@agent
	def reporting_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['reporting_analyst'],
			verbose=True,
			allow_delegation=False
		)

	@task
	def collect_clinical_features(self) -> Task:
		return Task(
			config=self.tasks_config['collect_clinical_features'],
		)

	@task
	def determine_epidemiology(self) -> Task:
		return Task(
			config=self.tasks_config['determine_epidemiology'],
			output_file='report.md'
		)
	
	@task
	def review_pathophysiology(self) -> Task:
		return Task(
			config=self.tasks_config['review_pathophysiology'],
		)
	
	@task
	def familiarize_diagnostic_workup(self) -> Task:
		return Task(
			config=self.tasks_config['familiarize_diagnostic_workup'],
		)
	
	@task
	def review_management_approaches(self) -> Task:
		return Task(
			config=self.tasks_config['review_management_approaches'],
		)
	
	@task
	def recognize_complications(self) -> Task:
		return Task(
			config=self.tasks_config['recognize_complications'],
		)
	
	@task
	def synthesize_information(self) -> Task:
		return Task(
			config=self.tasks_config['synthesize_information'],
			output_file='final_report.md'
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the DiseaseReview crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)